# adapters.py
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


class RestApiAdapter(BaseAdapter):
    def fetch(self) -> list[dict[str, Any]]:
        if not self.cfg.endpoint:
            raise ValueError("RestApiAdapter requires an endpoint.")
        response = httpx.get(self.cfg.endpoint, timeout=30)
        response.raise_for_status()
        data = response.json()
        # normalize to list
        return data if isinstance(data, list) else data.get("items", [data])


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


ADAPTER_REGISTRY: dict[str, type[BaseAdapter]] = {
    "rest_api": RestApiAdapter,
    "static": StaticAdapter,
}


def get_adapter(cfg: SourceConfig) -> BaseAdapter:
    cls = ADAPTER_REGISTRY.get(cfg.adapter)
    if not cls:
        raise ValueError(f"Unknown adapter: '{cfg.adapter}'. "
                         f"Available: {list(ADAPTER_REGISTRY)}")
    return cls(cfg)
