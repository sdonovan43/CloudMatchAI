from __future__ import annotations
from typing import Any
import asyncio
import httpx
import json


# ============================
#   UNIFIED LLM PROVIDER LAYER
# ============================

class BaseLLMProvider:
    """Abstract interface all providers must follow."""
    def __init__(self, cfg):
        self.cfg = cfg

    async def chat(self, messages: list[dict]) -> str:
        raise NotImplementedError


# ----------------------------
#   OpenAI Provider
# ----------------------------

class OpenAIProvider(BaseLLMProvider):
    async def chat(self, messages: list[dict]) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.cfg.llm.endpoint}/chat/completions",
                headers={"Authorization": f"Bearer {self.cfg.llm.api_key}"},
                json={
                    "model": self.cfg.llm.model,
                    "messages": messages,
                    "temperature": 0.0,
                    "stream": False,
                },
            )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ----------------------------
#   Groq Provider
# ----------------------------

class GroqProvider(BaseLLMProvider):
    async def chat(self, messages: list[dict]) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            # Debug output
            print("\n=== GROQ REQUEST DEBUG ===")
            print("Model:", self.cfg.llm.model)
            print("Messages:", messages)
            print("==========================\n")

            resp = await client.post(
                f"{self.cfg.llm.endpoint}/chat/completions",
                headers={"Authorization": f"Bearer {self.cfg.llm.api_key}"},
                json={
                    "model": self.cfg.llm.model,
                    "messages": messages,
                    "temperature": 0.0,
                    "stream": False,
                    "max_tokens": 256, 
                },
            )

        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ----------------------------
#   Azure OpenAI Provider
# ----------------------------

class AzureOpenAIProvider(BaseLLMProvider):
    async def chat(self, messages: list[dict]) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.cfg.llm.endpoint}/openai/deployments/{self.cfg.llm.model}/chat/completions?api-version=2024-02-01",
                headers={"api-key": self.cfg.llm.api_key},
                json={
                    "messages": messages,
                    "temperature": 0.0,
                    "stream": False,
                },
            )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ----------------------------
#   Local Ollama Provider
# ----------------------------

class OllamaProvider(BaseLLMProvider):
    async def chat(self, messages: list[dict]) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.cfg.llm.endpoint}/chat",
                json={
                    "model": self.cfg.llm.model,
                    "messages": messages,
                    "stream": False,
                },
            )
        resp.raise_for_status()
        return resp.json()["message"]["content"]


# ----------------------------
#   Gemini Provider
# ----------------------------

class GeminiProvider(BaseLLMProvider):
    async def chat(self, messages: list[dict]) -> str:
        """
        Executes a completion request using Google's native developer API syntax.
        Converts generic OpenAI roles into Gemini's contents/system_instruction format.
        """
        contents = []
        system_instruction = None

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})

        # Base URL for Google Developer standard endpoints
        base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        url = f"{base_url}/{self.cfg.llm.model}:generateContent?key={self.cfg.llm.api_key}"

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }

        if system_instruction:
            payload["systemInstruction"] = system_instruction

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            
            resp_data = resp.json()
            return resp_data["candidates"][0]["content"]["parts"][0]["text"]


# ============================
#   REGISTRY & ORCHESTRATION
# ============================

PROVIDERS = {
    "openai": OpenAIProvider,
    "groq": GroqProvider,
    "azure": AzureOpenAIProvider,
    "ollama": OllamaProvider,
    "gemini": GeminiProvider,
}

def _get_provider(cfg) -> BaseLLMProvider:
    cls = PROVIDERS.get(cfg.llm.provider.lower())
    if not cls:
        raise ValueError(f"Unknown LLM provider: {cfg.llm.provider}")
    return cls(cfg)


async def score_entities(cfg: Any, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Orchestrates the asynchronous evaluation pipeline.
    Passes criteria to the provider and maps matching scores back to elements.
    Includes an aggressive backoff pacing mechanism optimized for free-tier quotas.
    """
    if not items:
        return []

    provider = _get_provider(cfg)
    scored_items = []

    system_prompt = (
        "You are an expert procurement and cloud architecture analyzer. "
        "Analyze the given entities and score them strictly on the criteria weights provided. "
        "Return data exclusively as a JSON object matching requested criteria formatting."
    )

    for i, item in enumerate(items):
        # --- PACE FREE-TIER REQUESTS ---
        # Pause before EVERY Gemini call (including the first) so a fresh run
        # doesn't immediately land inside a rate-limit window left over from
        # a previous run.
        if cfg.llm.provider.lower() == "gemini":
            await asyncio.sleep(4.0)

        user_prompt = (
            f"Profile Context:\n"
            f"Name: {cfg.profile.name}\n"
            f"Description: {cfg.profile.description}\n"
            f"Target Weights: {json.dumps(cfg.profile.criteria)}\n\n"
            f"Entity to Score:\n{json.dumps(item, indent=2)}\n\n"
            f"Provide matching scores (0.0 to 1.0) and a brief raw string reasoning explanation."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        max_retries = 3
        attempt = 0
        success = False
        parsed_scores = None

        while attempt < max_retries and not success:
            try:
                raw_response = await provider.chat(messages)
                try:
                    parsed_scores = json.loads(raw_response)
                    success = True
                except json.JSONDecodeError as e:
                    # This is the case that was previously silent: the HTTP call
                    # succeeded (status 200) but the body wasn't valid JSON —
                    # e.g. wrapped in ```json fences, or an error message in prose.
                    print(f"SCORER PARSE ERROR: '{item.get('name', 'Unknown')}' returned non-JSON.")
                    print(f"  Raw response (first 500 chars): {raw_response[:500]!r}")
                    break
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                body_preview = e.response.text[:500]
                print(f"SCORER HTTP ERROR: '{item.get('name', 'Unknown')}' got status {status}")
                print(f"  Response body (first 500 chars): {body_preview!r}")

                if status in (429, 503):
                    attempt += 1
                    # Prefer the server's own Retry-After header if present —
                    # Google will sometimes tell you exactly how long to wait.
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after is not None:
                        try:
                            backoff_time = float(retry_after)
                        except ValueError:
                            backoff_time = 15.0 * attempt
                    else:
                        # Aggressive backoff: Attempt 1 = 15s, Attempt 2 = 30s, Attempt 3 = 45s
                        backoff_time = 15.0 * attempt
                    print(f"SCORER RETRY: Backing off for {backoff_time}s... (Attempt {attempt}/{max_retries})")
                    await asyncio.sleep(backoff_time)
                else:
                    print(f"SCORER ERROR: Unrecoverable HTTPStatusError (Status: {status}) for '{item.get('name', 'Unknown')}'")
                    break
            except Exception as e:
                print(f"SCORER ERROR: Unrecoverable processing error for '{item.get('name', 'Unknown')}': {type(e).__name__}: {e}")
                break

        if success and parsed_scores:
            enriched_item = item.copy()
            enriched_item["_match_analysis"] = parsed_scores
            scored_items.append(enriched_item)
        else:
            print(f"SCORER FATAL: Skipping entity '{item.get('name', 'Unknown')}' completely after exhausted retry limits.")
            fallback = item.copy()
            fallback["_match_analysis"] = {"error": "Failed to generate scores after multiple backend attempts."}
            scored_items.append(fallback)

    return scored_items