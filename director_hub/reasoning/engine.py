"""Reasoning Engine - the LLM that interprets player input.

SCAFFOLDING STUB. Real implementation tracked in spec §14 follow-up #2
(LLM provider selection). For now this returns a deterministic fallback
decision so the rest of the system can be wired up and tested.
"""
from __future__ import annotations

from typing import Any


class ReasoningEngine:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def interpret(self, action_request: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "session_id": action_request.get("session_id", ""),
            "success": True,
            "scale": 5,
            "narrative_text": (
                f"[stub] You attempted: {action_request.get('player_input', '')!r}. "
                "The reasoning engine is not yet implemented; deterministic fallback in effect."
            ),
            "stat_effects": [],
            "fx_requests": [],
            "repetition_penalty": 0,
            "deterministic_fallback": True,
        }
