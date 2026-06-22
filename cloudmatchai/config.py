# config.py
from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    adapter: str
    endpoint: str | None = None
    fields: list[str] = Field(default_factory=list)


class ProfileConfig(BaseModel):
    workload: str | None = None
    budget_monthly_usd: float | None = None
    requirements: list[str] = Field(default_factory=list)
    weights: dict[str, float] = Field(default_factory=dict)


class OutputConfig(BaseModel):
    storage: str = "sqlite"
    dashboard: bool = True
    webhook: str | None = None


class MatchConfig(BaseModel):
    source: SourceConfig
    profile: ProfileConfig
    output: OutputConfig = Field(default_factory=OutputConfig)


def load_config(path: str | Path) -> MatchConfig:
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text())
    return MatchConfig(**raw)
