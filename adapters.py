from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
import httpx
from config import SourceConfig


class BaseAdapter(ABC):
    def __init__(self, cfg: SourceConfig):
        self.cfg = cfg

    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]:
        """Return a list of candidate records."""
        ...


# ============================
#       GROQ ADAPTER
# ============================

class GroqAdapter(BaseAdapter):
    """
    Adapter for Groq's OpenAI-compatible API.
    Sends a minimal chat request and expects the model
    to return a JSON list of entities.
    """

    def fetch(self) -> list[dict[str, Any]]:
        endpoint = self.cfg.endpoint

        headers = {
            "Authorization": f"Bearer {self.cfg.llm.api_key}",
            "Content-Type": "application/json",
        }

        # Minimal Groq request — model must return a JSON list
        payload = {
            "model": self.cfg.llm.model,
            "messages": [
                {
                    "role": "user",
                    "content": "Return a JSON list of entities to score."
                }
            ],
            "temperature": 0.0,
        }

        try:
            resp = httpx.post(endpoint, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # If Groq returns a raw list
            if isinstance(data, list):
                return data

            # If Groq returns OpenAI-style structure
            if isinstance(data, dict):
                try:
                    content = data["choices"][0]["message"]["content"]
                    # Parse the content as JSON
                    return httpx.Response.json(httpx.Response(200, text=content))
                except Exception:
                    pass

            return []

        except Exception as e:
            print("GROQ ADAPTER ERROR:", e)
            return []


# ============================
#       REST API ADAPTER
# ============================

class RestAPIAdapter(BaseAdapter):
    """Generic REST adapter for JSON APIs."""
    def fetch(self) -> list[dict[str, Any]]:
        try:
            response = httpx.get(self.cfg.endpoint, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Normalize to list
            if isinstance(data, list):
                return data

            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        return v

            return []

        except Exception as e:
            print("REST API ERROR:", e)
            return []


# ============================
#       STATIC ADAPTER
# ============================

class StaticAdapter(BaseAdapter):
    """Drop-in adapter for local testing — returns hardcoded sample data."""
    def fetch(self) -> list[dict[str, Any]]:
        return [
            {"name": "AWS", "compute": "high", "storage": "high",
             "egress": "high", "regions": 30, "compliance": ["SOC2", "GDPR"]},
            {"name": "Azure", "compute": "high", "storage": "medium",
             "egress": "medium", "regions": 28, "compliance": ["SOC2", "GDPR"]},
            {"name": "GCP", "compute": "medium", "storage": "medium",
             "egress": "low", "regions": 25, "compliance": ["SOC2"]},
        ]


# ============================
#       ADAPTER REGISTRY
# ============================

ADAPTERS: dict[str, type[BaseAdapter]] = {
    "rest_api": RestAPIAdapter,
    "static": StaticAdapter,
    "groq": GroqAdapter,
}


def get_adapter(cfg: SourceConfig) -> BaseAdapter:
    cls = ADAPTERS.get(cfg.adapter)
    if not cls:
        raise ValueError(
            f"Unknown adapter: '{cfg.adapter}'. Available: {list(ADAPTERS)}"
        )
    return cls(cfg)
