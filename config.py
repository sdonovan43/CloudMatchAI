from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
import yaml


class SourceConfig(BaseModel):
    adapter: str
    endpoint: Optional[str] = None


class MatchProfile(BaseModel):
    name: str
    description: str
    criteria: dict


class ProfileConfig(BaseModel):
    source: SourceConfig
    profile: MatchProfile


def load_config(path: str) -> ProfileConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return ProfileConfig(**data)
