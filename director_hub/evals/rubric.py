"""Rubric-based evaluation.

Scores a trace (the list of spans the Tracer collected during one
LoopController step) against a fixed rubric. Returns a float in [0, 1]
where 1 is "all four phases ran cleanly with no flags" and 0 is "the
loop was a complete failure".

The rubric is fixed (not LLM-generated) so it's deterministic and runs
in CI without an API key. A future spec could add a Vertex-AI-style
adaptive rubric that the LLM generates per-task and validates per-task.
"""

from __future__ import annotations

from typing import Any

# How much each phase + each quality signal contributes to the final score
_PHASE_WEIGHTS = {
    "observe": 0.2,
    "reason+act": 0.5,
    "reflect": 0.2,
}
_NO_FAILURE_BONUS = 0.1


class Rubric:
    def score(self, trace: list[dict[str, Any]]) -> float:
        if not trace:
            return 0.0

        total = 0.0
        seen_phases: set[str] = set()
        any_failure = False

        for span in trace:
            phase = span.get("phase")
            if phase in _PHASE_WEIGHTS and phase not in seen_phases:
                total += _PHASE_WEIGHTS[phase]
                seen_phases.add(phase)
            if span.get("failure_tag"):
                any_failure = True

        if not any_failure and "reflect" in seen_phases:
            total += _NO_FAILURE_BONUS

        return min(1.0, max(0.0, total))

    def explain(self, trace: list[dict[str, Any]]) -> dict[str, Any]:
        """Return a structured breakdown of the score for debugging."""
        if not trace:
            return {"score": 0.0, "phases_seen": [], "failures": [], "notes": ["empty trace"]}

        seen: list[str] = []
        failures: list[str] = []
        for span in trace:
            phase = span.get("phase")
            if phase and phase not in seen:
                seen.append(phase)
            tag = span.get("failure_tag")
            if tag:
                failures.append(str(tag))

        score = self.score(trace)
        return {
            "score": score,
            "phases_seen": seen,
            "failures": failures,
            "notes": [
                f"saw {len(seen)} unique phases",
                f"{len(failures)} failure tags",
            ],
        }
