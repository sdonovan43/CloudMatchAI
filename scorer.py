from __future__ import annotations
from typing import Any
import httpx
import json


# ============================
#   UNIFIED LLM PROVIDER LAYER
# ============================

class BaseLLMProvider:
    """Abstract interface all providers must follow."""
    def __init__(self, cfg):
        self.cfg = cfg

    async def chat(self, messages: list[dict]) -> str:
        raise NotImplementedError


# ----------------------------
#   OpenAI Provider
# ----------------------------

class OpenAIProvider(BaseLLMProvider):
    async def chat(self, messages: list[dict]) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.cfg.llm.endpoint}/chat/completions",
                headers={"Authorization": f"Bearer {self.cfg.llm.api_key}"},
                json={
                    "model": self.cfg.llm.model,
                    "messages": messages,
                    "temperature": 0.0,
                    "stream": False,
                },
            )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ----------------------------
#   Groq Provider
# ----------------------------

class GroqProvider(BaseLLMProvider):
    async def chat(self, messages: list[dict]) -> str:
        async with httpx.AsyncClient(timeout=30) as client:

            # Debug output
            print("\n=== GROQ REQUEST DEBUG ===")
            print("Model:", self.cfg.llm.model)
            print("Messages:", messages)
            print("==========================\n")

            resp = await client.post(
                f"{self.cfg.llm.endpoint}/chat/completions",
                headers={"Authorization": f"Bearer {self.cfg.llm.api_key}"},
                json={
                    "model": self.cfg.llm.model,
                    "messages": messages,
                    "temperature": 0.0,
                    "stream": False,
                    "max_tokens": 256, 
                },
            )

        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ----------------------------
#   Azure OpenAI Provider
# ----------------------------

class AzureOpenAIProvider(BaseLLMProvider):
    async def chat(self, messages: list[dict]) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.cfg.llm.endpoint}/openai/deployments/{self.cfg.llm.model}/chat/completions?api-version=2024-02-01",
                headers={"api-key": self.cfg.llm.api_key},
                json={
                    "messages": messages,
                    "temperature": 0.0,
                    "stream": False,
                },
            )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ----------------------------
#   Local Ollama Provider
# ----------------------------

class OllamaProvider(BaseLLMProvider):
    async def chat(self, messages: list[dict]) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.cfg.llm.endpoint}/chat",
                json={
                    "model": self.cfg.llm.model,
                    "messages": messages,
                    "stream": False,
                },
            )
        resp.raise_for_status()
        return resp.json()["message"]["content"]


# ----------------------------
#   Gemini Provider
# ----------------------------

class GeminiProvider(BaseLLMProvider):
    async def chat(self, messages: list[dict]) -> str:
        """
        Executes a completion request using Google's native developer API syntax.
        Converts generic OpenAI roles into Gemini's contents/system_instruction format.
        """
        contents = []
        system_instruction = None

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]Normally I can help with things like this, but I don't seem to have access to that content. You can try again or ask me for something else.