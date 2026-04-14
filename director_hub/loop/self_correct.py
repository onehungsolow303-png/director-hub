"""Self-correction: re-plan on tool failure or low-confidence result.

The LoopController calls SelfCorrector.should_replan(result) after each
step. If True, the controller will run another step against the same
observation. The retry budget is bounded by max_replans to prevent
runaway loops on persistent failures.

A real implementation could feed the failure trace back to the LLM
provider and ask for a corrected plan. This implementation uses
deterministic rules: re-plan if the result is missing essential fields,
has an out-of-range scale, has been flagged with a non-recoverable
FailureTag, or hit a tool timeout.
"""

from __future__ import annotations

from typing import Any

from director_hub.observability.failure_tags import FailureTag

_RECOVERABLE_FLAGS = {
    FailureTag.TOOL_API_TIMEOUT.value,
    FailureTag.PLANNING_LOOP.value,
    FailureTag.MISINTERPRETED_GOAL.value,
}


class SelfCorrector:
    max_replans = 3

    def should_replan(self, result: dict[str, Any]) -> bool:
        if not isinstance(result, dict):
            return True

        narrative = result.get("narrative_text", "")
        if not isinstance(narrative, str) or not narrative.strip():
            return True

        scale = result.get("scale")
        if not isinstance(scale, int) or scale < 1 or scale > 10:
            return True

        flag = result.get("failure_tag")
        if isinstance(flag, str) and flag in _RECOVERABLE_FLAGS:
            return True

        return False
