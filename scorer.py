from __future__ import annotations
from typing import Any
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
#   Provider Router
# ----------------------------

LLM_PROVIDERS = {
    "openai": OpenAIProvider,
    "groq": GroqProvider,
    "azure": AzureOpenAIProvider,
    "ollama": OllamaProvider,
}

def get_llm_provider(cfg):
    provider_name = cfg.llm.provider.lower()
    cls = LLM_PROVIDERS.get(provider_name)
    if not cls:
        raise ValueError(
            f"Unknown LLM provider '{provider_name}'. "
            f"Available: {list(LLM_PROVIDERS)}"
        )
    return cls(cfg)


# ============================
#       SCORING ENGINE
# ============================

async def score_entities(cfg, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Applies weighted scoring + LLM explanation.
    Returns ranked list of entities with breakdown + explanation.
    """

    criteria = cfg.profile.criteria
    provider = get_llm_provider(cfg)

    results = []

    for entity in entities:
        # ----------------------------
        #   Weighted numeric scoring
        # ----------------------------
        breakdown = {}
        total_score = 0.0

        for key, weight in criteria.items():
            raw_value = entity.get(key)

            if isinstance(raw_value, (int, float)):
                score = float(raw_value)
            elif isinstance(raw_value, str):
                mapping = {"low": 0.3, "medium": 0.6, "high": 0.9}
                score = mapping.get(raw_value.lower(), 0.5)
            else:
                score = 0.5

            breakdown[key] = score
            total_score += score * weight

        # ----------------------------
        #   LLM Explanation
        # ----------------------------
        breakdown_json = json.dumps(breakdown)

        prompt = (
            f"Explain why the score {total_score:.2f} makes sense "
            f"based on this breakdown: {breakdown_json}."
        )

        explanation = await provider.chat([
            {"role": "system", "content": "You are a precise scoring analyst."},
            {"role": "user", "content": prompt},
        ])

        results.append({
            "entity": entity,
            "score": round(total_score, 4),
            "breakdown": breakdown,
            "explanation": explanation,
        })

    return sorted(results, key=lambda r: r["score"], reverse=True)
