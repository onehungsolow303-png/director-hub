"""Inline reflection — fast post-decision evaluation that stores lessons."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from director_hub.reasoning.outcome import ComparisonResult

if TYPE_CHECKING:
    from director_hub.memory.manager import MemoryManager

log = logging.getLogger(__name__)


class InlineReflector:
    def __init__(self, manager: MemoryManager) -> None:
        self._mgr = manager

    def reflect(
        self,
        comparison: ComparisonResult,
        decision_summary: str,
        use_llm: bool = True,
    ) -> dict[str, Any] | None:
        """Run fast inline reflection. Stores lessons for surprises, skips routine outcomes."""
        if not comparison.should_store:
            log.debug("No surprises for %s — skipping reflection", comparison.decision_id)
            return None

        if use_llm:
            return self._reflect_with_llm(comparison, decision_summary)

        return self._reflect_deterministic(comparison, decision_summary)

    def _reflect_deterministic(
        self,
        comparison: ComparisonResult,
        decision_summary: str,
    ) -> dict[str, Any]:
        """Deterministic reflection (no LLM call). Used in tests and fallback."""
        lessons: list[str] = []

        for surprise in comparison.surprises:
            lesson = (
                f"Surprise ({surprise.type}): expected {surprise.expected}, "
                f"got {surprise.actual}. Context: {decision_summary}"
            )
            lessons.append(lesson)
            self._mgr.long.index(
                {
                    "text": lesson,
                    "category": "lesson",
                    "decision_id": comparison.decision_id,
                    "surprise_type": surprise.type,
                    "significance": surprise.significance,
                    "metadata": {"confirmed_count": 1},
                }
            )

        for signal in comparison.player_signals:
            lesson = f"Player signal ({signal.type}): {signal.actual}. Context: {decision_summary}"
            lessons.append(lesson)
            self._mgr.long.index(
                {
                    "text": lesson,
                    "category": "player_signal",
                    "decision_id": comparison.decision_id,
                    "signal_type": signal.type,
                    "metadata": {"confirmed_count": 1},
                }
            )

        log.info("Reflection stored %d lessons for %s", len(lessons), comparison.decision_id)
        return {"lessons_stored": len(lessons), "lessons": lessons}

    def _reflect_with_llm(
        self,
        comparison: ComparisonResult,
        decision_summary: str,
    ) -> dict[str, Any]:
        """LLM-powered reflection using Haiku for fast analysis."""
        try:
            import anthropic as anthropic_sdk

            from director_hub.reasoning.providers.anthropic import _resolve_anthropic_key
        except (ImportError, Exception):
            log.warning("LLM unavailable for reflection, falling back to deterministic")
            return self._reflect_deterministic(comparison, decision_summary)

        api_key = _resolve_anthropic_key()
        if not api_key:
            return self._reflect_deterministic(comparison, decision_summary)

        surprises_text = "\n".join(
            f"- {s.type}: expected {s.expected}, got {s.actual} (significance: {s.significance})"
            for s in comparison.surprises + comparison.player_signals
        )

        prompt = (
            f"You just made a game director decision. Here's what happened:\n\n"
            f"Decision: {decision_summary}\n"
            f"Surprises:\n{surprises_text}\n\n"
            f"Answer briefly in JSON:\n"
            f'{{"lesson": "one sentence lesson or null", '
            f'"rule_update": "semantic key to update or null", '
            f'"rule_value": "new value or null"}}'
        )

        try:
            client = anthropic_sdk.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            text = getattr(resp.content[0], "text", "") if resp.content else ""

            from director_hub.reasoning.providers.anthropic import _extract_json_object

            parsed = _extract_json_object(text)
            if parsed and parsed.get("lesson"):
                self._mgr.long.index(
                    {
                        "text": parsed["lesson"],
                        "category": "lesson",
                        "decision_id": comparison.decision_id,
                        "metadata": {"confirmed_count": 1},
                    }
                )

            if parsed and parsed.get("rule_update") and parsed.get("rule_value"):
                self._mgr.semantic.set(parsed["rule_update"], parsed["rule_value"])

            return {"lessons_stored": 1 if parsed and parsed.get("lesson") else 0, "llm_used": True}

        except Exception:
            log.exception("LLM reflection failed, falling back to deterministic")
            return self._reflect_deterministic(comparison, decision_summary)
