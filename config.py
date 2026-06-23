from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import BaseModel
import yaml


# ----------------------------
#   Source block
# ----------------------------

class SourceConfig(BaseModel):
    adapter: str
    endpoint: Optional[str] = None


# ----------------------------
#   Profile block
# ----------------------------

class MatchProfile(BaseModel):
    name: str
    description: str
    criteria: Dict[str, float]


# ----------------------------
#   LLM block
# ----------------------------

class LLMConfig(BaseModel):
    provider: str
    endpoint: str
    model: str
    api_key: str


# ----------------------------
#   Root config
# ----------------------------

class RootConfig(BaseModel):
    source: SourceConfig
    profile: MatchProfile
    llm: LLMConfig


# ----------------------------
#   Loader
# ----------------------------

def load_config(path: str) -> RootConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return RootConfig(**data)
