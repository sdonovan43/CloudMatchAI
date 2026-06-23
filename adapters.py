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
    Fetches JSON data from a REST endpoint and normalizes it into a list.
    """

    def fetch(self) -> list[dict[str, Any]]:
        # FIXED: SourceConfig has endpoint/method/headers/params directly
        endpoint = self.cfg.endpoint
        method = self.cfg.method.upper()
        headers = self.cfg.headers or {}
        params = self.cfg.params or {}

        # Inject Groq API key
        headers["Authorization"] = f"Bearer {self.cfg.llm.api_key}"

        try:
            if method == "GET":
                resp = httpx.get(endpoint, headers=headers, params=params, timeout=30)
            else:
                resp = httpx.post(endpoint, headers=headers, json=params, timeout=30)

            resp.raise_for_status()
            data = resp.json()

            # Normalize to list
            if isinstance(data, list):
                return data

            if isinstance(data, dict):
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

ADAPTERS: dict[str, type