from __future__ import annotations
from typing import Any
import httpx


# ============================
#   UNIFIED LLM PROVIDER LAYER
# ============================

class BaseLLMProvider:
    """Abstract interface all providers must follow."""
    def __init__(self, cfg):
        self.cfg = cfg

    def chat(self, messages: list[dict]) -> str:
        raise NotImplementedError


# ----------------------------
#   OpenAI Provider
# ----------------------------

class OpenAIProvider(BaseLLMProvider):
    def chat(self, messages: list[dict]) -> str:
        resp = httpx.post(
            f"{self.cfg.llm.endpoint}/chat/completions",
            headers={"Authorization": f"Bearer {self.cfg.llm.api_key}"},
            json={
                "model": self.cfg.llm.model,
                "messages": messages,
                "temperature": 0.0,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ----------------------------
#   Groq Provider
# ----------------------------

class GroqProvider(BaseLLMProvider):
    def chat(self, messages: list[dict]) -> str:
        resp = httpx.post(
            f"{self.cfg.llm.endpoint}/chat/completions",
            headers={"Authorization": f"Bearer {self.cfg.llm.api_key}"},
            json={
                "model": self.cfg.llm.model,
                "messages": messages,
                "temperature": 0.0,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ----------------------------
#   Azure OpenAI Provider
# ----------------------------

class AzureOpenAIProvider(BaseLLMProvider):
    def chat(self, messages: list[dict]) -> str:
        resp = httpx.post(
            f"{self.cfg.llm.endpoint}/openai/deployments/{self.cfg.llm.model}/chat/completions?api-version=2024-02-01",
            headers={"api-key": self.cfg.llm.api_key},
            json={
                "messages": messages,
                "temperature": 0.0,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ----------------------------
#   Local Ollama Provider
# ----------------------------

class OllamaProvider(BaseLLMProvider):
    def chat(self, messages: list[dict]) -> str:
        resp = httpx.post(
            f"{self.cfg.llm.endpoint}/chat",
            json={
                "model": self.cfg.llm.model,
                "messages": messages,
            },
            timeout=30,
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

def score_entities(cfg, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
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

            # Normalize numeric-ish values
            if isinstance(raw_value, (int, float)):
                score = float(raw_value)
            elif isinstance(raw_value, str):
                # crude normalization for now
                mapping = {"low": 0.3, "medium": 0.6, "high": 0.9}
                score = mapping.get(raw_value.lower(), 0.5)
            else:
                score = 0.5

            breakdown[key] = score
            total_score += score * weight

        # ----------------------------
        #   LLM Explanation
        # ----------------------------
        prompt = (
            "You are a scoring engine. "
            "Given the following entity and its weighted scoring breakdown, "
            "explain the score in 3–5 sentences.\n\n"
            f"Entity: {entity}\n"
            f"Breakdown: {breakdown}\n"
            f"Final Score: {total_score:.2f}"
        )

        explanation = provider.chat([
            {"role": "system", "content": "You are a precise scoring analyst."},
            {"role": "user", "content": prompt},
        ])

        results.append({
            "entity": entity,
            "score": round(total_score, 4),
            "breakdown": breakdown,
            "explanation": explanation,
        })

    # Sort descending
    return sorted(results, key=lambda r: r["score"], reverse=True)
