from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence
from typing import Any

import httpx

from omega.schema import AgentMessage


class OpenRouterError(RuntimeError):
    """Raised when OpenRouter rejects or cannot complete a request."""


class OpenRouterClient:
    """Small async OpenRouter client with streaming and non-streaming chat support."""

    def __init__(self, api_key: str | None, base_url: str = "https://openrouter.ai/api/v1") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def available(self) -> bool:
        return bool(self.api_key)

    async def chat(
        self,
        *,
        model: str,
        messages: Sequence[AgentMessage],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        if not self.api_key:
            raise OpenRouterError("OPENROUTER_API_KEY is not configured.")
        payload = {
            "model": model,
            "messages": [message.model_dump(exclude_none=True) for message in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
            )
        if response.status_code >= 400:
            raise OpenRouterError(f"OpenRouter error {response.status_code}: {response.text}")
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def stream_chat(
        self,
        *,
        model: str,
        messages: Sequence[AgentMessage],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        if not self.api_key:
            raise OpenRouterError("OPENROUTER_API_KEY is not configured.")
        payload: dict[str, Any] = {
            "model": model,
            "messages": [message.model_dump(exclude_none=True) for message in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
            ) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    raise OpenRouterError(f"OpenRouter error {response.status_code}: {body.decode()}")
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line.removeprefix("data: ").strip()
                    if raw == "[DONE]":
                        break
                    event = json.loads(raw)
                    delta = event["choices"][0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/open-source/omega",
            "X-Title": "OMEGA",
        }
