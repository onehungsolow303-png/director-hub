"""Anthropic Claude provider.

Uses the official `anthropic` SDK. Requires:
  - `pip install anthropic`
  - ANTHROPIC_API_KEY environment variable

If either is missing, this provider raises ProviderUnavailable on construction
so the engine can fall back to the stub. It does NOT crash on import — the
import is lazy so the rest of director_hub stays installable on systems
without the SDK.

The prompt mirrors the spec's "AI for Interpretation" section: feed the
engine the player stats, target stats, scene context, and the player's
free-text input, then ask for a 1-10 success scale and a narrative.
"""
from __future__ import annotations

import json
import os
from typing import Any

from .base import ReasoningProvider


class ProviderUnavailable(Exception):
    """Raised when a provider can't initialize (missing SDK or credentials)."""


_SYSTEM_PROMPT = """You are the AI Game Master for an RPG. You receive the
player's free-text action plus their stats and the scene context. Interpret
the action against the static rules and return a JSON object with:

  - success      (bool)        Did the action succeed?
  - scale        (int 1-10)    How significant was the outcome?
  - narrative_text (string)    A vivid 1-3 sentence description of what happened.
  - stat_effects (list)        Each item: {target_id, stat, delta, status_effect?}
                                where stat is one of "hp", "attack", "defense", "status".
  - fx_requests  (list)        Each item: {kind, biome?, theme?} for any visual FX.
  - repetition_penalty (int)   Higher when the player has been repeating themselves.

Return ONLY the JSON object, no surrounding prose or code fences. Do NOT
invent new stat values; only suggest deltas. Penalize repetitive actions
to encourage player creativity.
"""


class AnthropicProvider(ReasoningProvider):
    name = "anthropic"

    def __init__(self, model: str = "claude-sonnet-4-5", max_tokens: int = 1024) -> None:
        try:
            import anthropic  # noqa: F401  (verify importable)
        except ImportError as e:
            raise ProviderUnavailable(
                f"anthropic SDK not installed: {e}. "
                "Run `pip install anthropic` to enable this provider."
            ) from e

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderUnavailable(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Set it before starting Director Hub to enable the Claude provider."
            )

        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def interpret(self, action_request: dict[str, Any]) -> dict[str, Any]:
        user_payload = json.dumps(
            {
                "actor_stats": action_request.get("actor_stats", {}),
                "target_stats": action_request.get("target_stats"),
                "scene_context": action_request.get("scene_context", {}),
                "recent_history": action_request.get("recent_history", []),
                "player_input": action_request.get("player_input", ""),
            },
            ensure_ascii=False,
        )

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_payload}],
            )
        except Exception as e:  # SDK can raise many subtypes; catch broadly at boundary
            raise ProviderUnavailable(f"Anthropic API call failed: {e}") from e

        # Extract the text response
        text_parts = [block.text for block in response.content if hasattr(block, "text")]
        raw = "".join(text_parts).strip()
        if raw.startswith("```"):
            # Strip optional code-fence wrapping
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:].strip()

        try:
            decision = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ProviderUnavailable(
                f"Anthropic response was not valid JSON: {e}. Raw: {raw!r}"
            ) from e

        # Defensive defaults — the model may omit some fields
        decision.setdefault("success", True)
        decision.setdefault("scale", 5)
        decision.setdefault("narrative_text", "")
        decision.setdefault("stat_effects", [])
        decision.setdefault("fx_requests", [])
        decision.setdefault("repetition_penalty", 0)
        return decision
