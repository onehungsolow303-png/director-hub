"""Deterministic stub provider.

Returns the same well-formed decision payload for any input. Used when
no real LLM provider is configured (or when the configured provider's
credentials are missing). This is the safety net the bridge falls back
to so the engine never returns 500 just because someone forgot an API key.
"""

from __future__ import annotations

from typing import Any

from .base import ReasoningProvider


class StubProvider(ReasoningProvider):
    name = "stub"

    @property
    def is_real(self) -> bool:
        return False

    def interpret(self, action_request: dict[str, Any]) -> dict[str, Any]:
        player_input = action_request.get("player_input", "")
        return {
            "success": True,
            "scale": 5,
            "narrative_text": (
                f"[stub] You attempted: '{player_input}'. "
                "The reasoning engine is running in deterministic-fallback "
                "mode (no live LLM provider configured)."
            ),
            "stat_effects": [],
            "fx_requests": [],
            "repetition_penalty": 0,
        }
