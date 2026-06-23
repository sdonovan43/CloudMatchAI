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


# Unified registry — the ONLY one
ADAPTERS: dict[str, type[BaseAdapter]] = {
    "rest_api": RestAPIAdapter,
    "static": StaticAdapter,
}


def get_adapter(cfg: SourceConfig) -> BaseAdapter:
    cls = ADAPTERS.get(cfg.adapter)
    if not cls:
        raise ValueError(
            f"Unknown adapter: '{cfg.adapter}'. Available: {list(ADAPTERS)}"
        )
    return cls(cfg)

