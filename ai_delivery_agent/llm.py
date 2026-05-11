from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ai_delivery_agent.config import Settings


@dataclass
class LLMResponse:
    text: str
    used_mock: bool


class LLMClient:
    """Thin wrapper around an optional hosted LLM.

    If OPENAI_API_KEY is absent, this client returns deterministic mock text.
    That keeps the MVP runnable in a clean local environment.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.enabled = bool(settings.openai_api_key)
        self._client = None

        if self.enabled:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=settings.openai_api_key)
            except Exception as exc:  # pragma: no cover - depends on local package setup
                self.enabled = False
                self._client = None
                self._startup_error = str(exc)
            else:
                self._startup_error = ""
        else:
            self._startup_error = ""

    def complete(self, system: str, user: str, *, max_tokens: int = 1600) -> LLMResponse:
        if not self.enabled or self._client is None:
            return LLMResponse(
                text=(
                    "Mock LLM mode. Set OPENAI_API_KEY to enable repository-specific "
                    "reasoning and patch generation."
                ),
                used_mock=True,
            )

        try:
            completion = self._client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
                max_tokens=max_tokens,
            )
            text = completion.choices[0].message.content or ""
            return LLMResponse(text=text, used_mock=False)
        except Exception as exc:
            return LLMResponse(
                text=f"LLM call failed. Falling back to mock behavior. Error: {exc}",
                used_mock=True,
            )
