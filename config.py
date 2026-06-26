from __future__ import annotations
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import yaml
import os
import re


# ----------------------------
#   Source block
# ----------------------------

class SourceConfig(BaseModel):
    adapter: str
    url: str
    method: str = "GET"
    headers: dict[str, Any] = {}
    params: dict[str, Any] = {}


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
    model: str
    api_key: str
    endpoint: Optional[str] = None  # Optional to natively support Gemini/Google SDK environments


# ----------------------------
#   Storage block
# ----------------------------

class StorageConfig(BaseModel):
    path: str = "output.json"


# ----------------------------
#   Root config
# ----------------------------

class RootConfig(BaseModel):
    source: SourceConfig
    profile: MatchProfile
    llm: LLMConfig
    storage: StorageConfig = Field(default_factory=StorageConfig)


# ----------------------------
#   Environment variable resolver
# ----------------------------

ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")

def resolve_env(value):
    """Replace ${VAR} with environment variable VAR."""
    if isinstance(value, str):
        match = ENV_PATTERN.fullmatch(value)
        if match:
            var = match.group(1)
            resolved = os.getenv(var)
            if resolved is None:
                raise ValueError(f"Environment variable '{var}' is not set.")
            return resolved
    return value

def deep_resolve_env(obj):
    """Recursively resolve env vars in dicts/lists."""
    if isinstance(obj, dict):
        return {k: deep_resolve_env(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_resolve_env(v) for v in obj]
    return resolve_env(obj)


# ----------------------------
#   Loader
# ----------------------------

def load_config(path: str) -> RootConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    data = deep_resolve_env(data)
    return RootConfig(**data)