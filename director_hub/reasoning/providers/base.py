"""LLM provider ABC.

Every provider implements interpret(action_request) -> decision dict. The
decision dict must validate against C:/Dev/.shared/schemas/decision.schema.json.
The base class handles the wrapping (schema_version, session_id propagation,
fallback flag) so individual providers only return the narrative + effects.
"""
from __future__ import annotations

import abc
from typing import Any


class ReasoningProvider(abc.ABC):
    """Abstract LLM provider for the Director Hub reasoning engine."""

    name: str = "provider"

    @abc.abstractmethod
    def interpret(self, action_request: dict[str, Any]) -> dict[str, Any]:
        """Return a DecisionPayload-shaped dict.

        The minimal shape required by the contract:
            {
                "success": bool,
                "scale": int (1-10),
                "narrative_text": str,
                "stat_effects": list[dict],
                "fx_requests": list[dict],
                "repetition_penalty": int,
                "deterministic_fallback": bool,
            }

        Implementations should NOT include schema_version or session_id —
        the ReasoningEngine wrapper adds those.
        """
        ...

    @property
    def is_real(self) -> bool:
        """True for live LLM providers, False for the deterministic stub.

        The bridge sets `deterministic_fallback=True` on the response when
        this is False, so callers know the answer is canned.
        """
        return True
