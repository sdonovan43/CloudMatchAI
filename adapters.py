from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
import httpx
from config import RootConfig


class BaseAdapter(ABC):
    def __init__(self, cfg: RootConfig):
        self.cfg = cfg

    @abstractmethod
    async def fetch(self) -> list[dict[str, Any]]:
        ...


# ============================
#       GROQ ADAPTER
# ============================

class GroqAdapter(BaseAdapter):
    """
    Adapter for Groq's OpenAI-compatible API.
    This adapter is for fetching ENTITIES, not scoring.
    """

    async def fetch(self) -> list[dict[str, Any]]:
        url = self.cfg.source.url  # correct field
        method = self.cfg.source.method.upper()
        headers = self.cfg.source.headers or {}
        params = self.cfg.source.params or {}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if method == "GET":
                    resp = await client.get(url, headers=headers, params=params)
                else:
                    resp = await client.post(url, headers=headers, json=params)

                resp.raise_for_status()
                data = resp.json()

                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    # try to extract list from dict
                    for v in data.values():
                        if isinstance(v, list):
                            return v

                return []

            except Exception as e:
                print("GROQ ADAPTER ERROR:", e)
                return []


# ============================
#       REST API ADAPTER
# ============================

class RestAPIAdapter(BaseAdapter):
    async def fetch(self) -> list[dict[str, Any]]:
        url = self.cfg.source.url
        method = self.cfg.source.method.upper()
        headers = self.cfg.source.headers or {}
        params = self.cfg.source.params or {}

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                if method == "GET":
                    resp = await client.get(url, headers=headers, params=params)
                else:
                    resp = await client.post(url, headers=headers, json=params)

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
    async def fetch(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "AWS",
                "compute": "high",
                "storage": "high",
                "egress": "high",
                "regions": 30,
                "compliance": ["SOC2", "GDPR"]
            },
            {
                "name": "Azure",
                "compute": "high",
                "storage": "medium",
                "egress": "medium",
                "regions": 28,
                "compliance": ["SOC2", "GDPR"]
            },
            {
                "name": "GCP",
                "compute": "medium",
                "storage": "medium",
                "egress": "low",
                "regions": 25,
                "compliance": ["SOC2"]
            },
        ]


# ============================
#       ADAPTER REGISTRY
# ============================

ADAPTERS = {
    "rest_api": RestAPIAdapter,
    "static": StaticAdapter,
    "groq": GroqAdapter,
}


def get_adapter(cfg: RootConfig):
    cls = ADAPTERS.get(cfg.source.adapter)
    if not cls:
        raise ValueError(f"Unknown adapter: {cfg.source.adapter}")
    return cls(cfg)