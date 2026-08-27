from __future__ import annotations
from typing import Any
import asyncio
import httpx
import json
import re


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
        endpoint = (self.cfg.llm.endpoint or "https://api.openai.com/v1").rstrip("/")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{endpoint}/chat/completions",
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
        endpoint = (self.cfg.llm.endpoint or "https://api.groq.com/openai/v1").rstrip("/")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{endpoint}/chat/completions",
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
        endpoint = self.cfg.llm.endpoint
        if not endpoint:
            raise ValueError("Azure OpenAI provider requires 'endpoint' to be set in configuration.")
        endpoint = endpoint.rstrip("/")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{endpoint}/openai/deployments/{self.cfg.llm.model}/chat/completions?api-version=2024-02-01",
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
        endpoint = (self.cfg.llm.endpoint or "http://localhost:11434").rstrip("/")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{endpoint}/chat",
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

        # Timeout bumped from 30s -> 60s: prompts that include a full candidate
        # profile (skills list, experience summary) are significantly larger
        # than the original cloud-provider test prompts, and were tipping over
        # the old 30s ceiling under normal (non-error) load.
        async with httpx.AsyncClient(timeout=60) as client:
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


def _extract_retry_delay(response: httpx.Response) -> float | None:
    """
    Figures out exactly how long to wait before retrying, using the most
    precise source available:
      1. A standard Retry-After header, if present.
      2. Gemini's structured error body, which includes a RetryInfo detail
         like {"@type": "...RetryInfo", "retryDelay": "35s"}.
      3. A "Please retry in 12.3s" style message buried in the error text,
         as a last-resort regex fallback.
    Returns None if nothing usable is found, so the caller can fall back
    to its own fixed backoff schedule.
    A 1-second buffer is added on top of whatever Google reports, since
    retrying at exactly the reported instant sometimes still gets a 429.
    """
    retry_after = response.headers.get("Retry-After")
    if retry_after is not None:
        try:
            return float(retry_after) + 1.0
        except ValueError:
            pass

    try:
        body = response.json()
        details = body.get("error", {}).get("details", [])
        for detail in details:
            delay_str = detail.get("retryDelay")
            if delay_str and delay_str.endswith("s"):
                return float(delay_str[:-1]) + 1.0
    except (ValueError, json.JSONDecodeError, AttributeError):
        pass

    try:
        text = response.text
        match = re.search(r"retry in ([\d.]+)s", text, re.IGNORECASE)
        if match:
            return float(match.group(1)) + 1.0
    except Exception:
        pass

    return None


async def score_entities(cfg: Any, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Orchestrates the asynchronous evaluation pipeline.
    Passes criteria (and, if present, a candidate profile) to the provider
    and maps matching scores back to elements. Includes an aggressive backoff
    pacing mechanism optimized for free-tier quotas.
    """
    if not items:
        return []

    provider = _get_provider(cfg)
    scored_items = []

    candidate = getattr(cfg, "candidate", None)

    candidate_block = ""
    if candidate is not None:
        candidate_block = (
            "\n\nCandidate Profile (match entities against THIS person's background):\n"
            f"Summary: {candidate.summary}\n"
            f"Skills: {', '.join(candidate.skills) if candidate.skills else 'Not specified'}\n"
            f"Years of experience: {candidate.experience_years if candidate.experience_years is not None else 'Not specified'}\n"
            f"Experience summary: {candidate.experience_summary}\n"
        )

    system_prompt = (
        "You are an expert evaluator scoring entities against a set of weighted criteria. "
        "Analyze the given entity and score it strictly on the criteria weights provided."
        + (
            " When a Candidate Profile is supplied, treat this as a job-matching task: "
            "score how well the entity (a job listing) fits the candidate's real skills, "
            "experience, and background — not a generic ideal candidate."
            if candidate is not None else ""
        )
        + "\n\n"
        "You MUST return ONLY a single JSON object, with NO markdown code fences, "
        "NO commentary, and NO text before or after the JSON.\n\n"
        "The JSON object MUST exactly match this schema, with one entry under \"scores\" "
        "for EVERY criterion listed in the Target Weights (never omit one, never add extras):\n\n"
        "{\n"
        '  "scores": {\n'
        '    "<criterion_name>": {\n'
        '      "score": <float between 0.0 and 1.0>,\n'
        '      "reasoning": "<one sentence explanation>"\n'
        "    }\n"
        "    // one entry per criterion, using the exact criterion names given\n"
        "  },\n"
        '  "overall_score": <float between 0.0 and 1.0, the weighted average across all criteria>\n'
        "}\n\n"
        "Do not rename \"scores\" or \"overall_score\". Do not nest differently. "
        "Do not add extra top-level keys."
    )

    for i, item in enumerate(items):
        # --- PACE FREE-TIER REQUESTS ---
        # Pause before EVERY Gemini call (including the first) so a fresh run
        # doesn't immediately land inside a rate-limit window left over from
        # a previous run.
        if cfg.llm.provider.lower() == "gemini":
            await asyncio.sleep(5.0)

        user_prompt = (
            f"Profile Context:\n"
            f"Name: {cfg.profile.name}\n"
            f"Description: {cfg.profile.description}\n"
            f"Target Weights: {json.dumps(cfg.profile.criteria)}"
            f"{candidate_block}\n\n"
            f"Entity to Score:\n{json.dumps(item, indent=2)}\n\n"
            f"You must include exactly these criteria keys under \"scores\", no more and no fewer: "
            f"{json.dumps(list(cfg.profile.criteria.keys()))}\n"
            f"Return ONLY the JSON object matching the schema described in the system prompt."
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
                cleaned_response = raw_response.strip()
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response.strip("`")
                    if cleaned_response.lower().startswith("json"):
                        cleaned_response = cleaned_response[4:]
                    cleaned_response = cleaned_response.strip()

                try:
                    parsed_scores = json.loads(cleaned_response)
                    success = True
                except json.JSONDecodeError:
                    print(f"SCORER PARSE ERROR: '{item.get('name', 'Unknown')}' returned non-JSON.")
                    print(f"  Raw response (first 500 chars): {raw_response[:500]!r}")
                    break

            except httpx.TimeoutException as e:
                # Was previously falling into the generic `except Exception` below
                # and giving up with zero retries. Timeouts are transient — retry
                # them the same way as 429/503.
                attempt += 1
                backoff_time = 10.0 * attempt
                print(f"SCORER TIMEOUT: '{item.get('name', 'Unknown')}' timed out ({type(e).__name__}).")
                print(f"  Backing off for {backoff_time}s... (Attempt {attempt}/{max_retries})")
                await asyncio.sleep(backoff_time)

            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                body_preview = e.response.text[:500]
                print(f"SCORER HTTP ERROR: '{item.get('name', 'Unknown')}' got status {status}")
                print(f"  Response body (first 500 chars): {body_preview!r}")

                if status in (429, 503):
                    attempt += 1
                    backoff_time = _extract_retry_delay(e.response) or (15.0 * attempt)
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