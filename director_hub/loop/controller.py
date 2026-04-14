"""Execution loop: observe -> reason -> act -> reflect.

Per spec §4 'Execution Loop (The Will)' from the original Director Hub
brief. Each call to step() runs the four phases against a single
observation (one player action) and emits a trace record describing
what happened at each phase.

The loop is intentionally lightweight — heavy lifting (LLM calls, dice
rolls, asset requests) happens inside the reasoning engine and the
toolbelt. This file orchestrates the four-phase rhythm and feeds the
tracer + failure tag system.

Phases:
  observe  - capture the input observation, attach a trace span
  reason   - call the ReasoningEngine to interpret the observation
  act      - the engine's response IS the action; we return it as the
             step result. (Tool calls happen INSIDE reason.)
  reflect  - evaluate the result against expectations, log to tracer,
             flag any failures via FailureTag
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from director_hub.observability.failure_tags import FailureTag
from director_hub.observability.tracer import Tracer
from director_hub.reasoning.engine import ReasoningEngine

logger = logging.getLogger(__name__)


class LoopController:
    def __init__(
        self,
        engine: ReasoningEngine | None = None,
        tracer: Tracer | None = None,
    ) -> None:
        # NOT `engine or ReasoningEngine()` because Tracer defines __len__
        # and is falsy when empty — `tracer or Tracer()` would silently
        # discard the caller's empty tracer. Same defensive check on engine
        # for symmetry.
        self._engine = engine if engine is not None else ReasoningEngine()
        self._tracer = tracer if tracer is not None else Tracer()

    @property
    def tracer(self) -> Tracer:
        return self._tracer

    def step(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Run one observe→reason→act→reflect cycle.

        Returns the DecisionPayload from the reasoning engine plus a
        `_trace_id` field the caller can use to look up the trace span
        in the tracer.
        """
        trace_id = str(uuid.uuid4())
        started = time.monotonic()

        # OBSERVE
        self._tracer.record(
            {
                "trace_id": trace_id,
                "phase": "observe",
                "observation_summary": _summarize(observation),
                "ts": time.time(),
            }
        )

        # REASON  +  ACT (the engine's response IS the action)
        try:
            decision = self._engine.interpret(observation)
            failure_tag: FailureTag | None = None
        except Exception as e:  # boundary
            logger.error("[LoopController] reason phase raised: %s", e)
            decision = {
                "schema_version": "1.0.0",
                "session_id": observation.get("session_id", ""),
                "success": False,
                "scale": 1,
                "narrative_text": f"(reasoning failed: {e})",
                "stat_effects": [],
                "fx_requests": [],
                "repetition_penalty": 0,
                "deterministic_fallback": True,
            }
            failure_tag = FailureTag.UNKNOWN

        self._tracer.record(
            {
                "trace_id": trace_id,
                "phase": "reason+act",
                "decision_summary": _summarize_decision(decision),
                "provider": self._engine.provider_name,
                "ts": time.time(),
            }
        )

        # REFLECT
        elapsed_ms = int((time.monotonic() - started) * 1000)
        reflection = _reflect(observation, decision, elapsed_ms)
        if reflection.get("flag") and failure_tag is None:
            failure_tag = reflection["flag"]

        self._tracer.record(
            {
                "trace_id": trace_id,
                "phase": "reflect",
                "elapsed_ms": elapsed_ms,
                "failure_tag": failure_tag.value if failure_tag else None,
                "notes": reflection.get("notes", []),
                "ts": time.time(),
            }
        )

        decision["_trace_id"] = trace_id
        return decision


def _summarize(observation: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": observation.get("session_id"),
        "actor_id": observation.get("actor_id"),
        "player_input_len": len(observation.get("player_input", "")),
        "has_target": observation.get("target_id") is not None,
    }


def _summarize_decision(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": decision.get("success"),
        "scale": decision.get("scale"),
        "narrative_len": len(decision.get("narrative_text", "")),
        "stat_effect_count": len(decision.get("stat_effects") or []),
        "deterministic_fallback": decision.get("deterministic_fallback"),
    }


def _reflect(
    observation: dict[str, Any],
    decision: dict[str, Any],
    elapsed_ms: int,
) -> dict[str, Any]:
    """Lightweight quality checks the loop runs after each step."""
    notes: list[str] = []
    flag: FailureTag | None = None

    if not decision.get("narrative_text"):
        notes.append("empty narrative_text")
        flag = FailureTag.MISINTERPRETED_GOAL

    scale = decision.get("scale")
    if not isinstance(scale, int) or scale < 1 or scale > 10:
        notes.append(f"scale {scale!r} out of range")
        flag = FailureTag.HALLUCINATION_FACTUAL

    if elapsed_ms > 5000:
        notes.append(f"slow response: {elapsed_ms}ms")
        flag = FailureTag.TOOL_API_TIMEOUT

    return {"flag": flag, "notes": notes}
