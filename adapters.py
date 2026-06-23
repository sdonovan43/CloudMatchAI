from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
import httpx
from config import Config  # root config, not SourceConfig


class BaseAdapter(ABC):
    def __init__(self, cfg: Config):
        self.cfg = cfg

    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]:
        ...


# ============================
#       GROQ ADAPTER
# ============================

class GroqAdapter(BaseAdapter):
    """
    Adapter for Groq's OpenAI-compatible API.
    """

    def fetch(self) -> list[dict[str, Any]]:
        endpoint = self.cfg.source.endpoint

        headers = {
            "Authorization": f"Bearer {self.cfg.llm.api_key}",
            "Content-Type": "application/json",
        }

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
    def fetch(self) -> list[dict[str, Any]]:
        try:
            resp = httpx.get(self.cfg.source.endpoint, timeout=10)
            resp.raise_for_status()
            data = resp.json()

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

ADAPTERS = {
    "rest_api": RestAPIAdapter,
    "static": StaticAdapter,
    "groq": GroqAdapter,
}


def get_adapter(cfg: Config):
    cls = ADAPTERS.get(cfg.source.adapter)
    if not cls:
        raise ValueError(f"Unknown adapter: {cfg.source.adapter}")
    return cls(cfg)
