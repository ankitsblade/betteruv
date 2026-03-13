from __future__ import annotations

import json
import os
from typing import Any

import httpx


class GroqClient:
    """Small Groq chat wrapper using the OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("BETTERUV_GROQ_MODEL", "llama-3.3-70b-versatile")
        timeout_from_env = os.getenv("BETTERUV_GROQ_TIMEOUT_SECONDS")
        if timeout_from_env:
            try:
                timeout_seconds = float(timeout_from_env)
            except ValueError:
                pass
        self.timeout_seconds = timeout_seconds
        self.base_url = os.getenv("BETTERUV_GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def chat_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 700,
    ) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url.rstrip('/')}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
        except Exception:
            # AI assist is best-effort. Dependency, transport, or provider failures
            # should fall back to local heuristics instead of breaking the CLI flow.
            return None

        try:
            content = data["choices"][0]["message"]["content"]
            if isinstance(content, dict):
                return content
            if isinstance(content, list):
                # Some OpenAI-compatible providers may return content parts.
                joined = "".join(
                    part.get("text", "") for part in content if isinstance(part, dict)
                )
                parsed = json.loads(joined)
                return parsed if isinstance(parsed, dict) else None
            if isinstance(content, str):
                parsed = json.loads(content)
                return parsed if isinstance(parsed, dict) else None
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            return None

        return None
