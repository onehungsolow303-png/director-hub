"""CI gate: blocks deploy if metrics regress past threshold.

Compares a baseline metrics dict against a current metrics dict. Returns
(passed, message) — passed=False indicates the deploy should be blocked.

Thresholds are configured in director_hub/config/thresholds.yaml and
overridable per-instance via the constructor.
"""

from __future__ import annotations

from typing import Any


class CIGate:
    """Compare current metrics against a baseline. Block on regression."""

    def __init__(
        self,
        tsr_drop_threshold: float = 0.05,
        latency_increase_ms: int = 100,
        hallucination_rate_max: float = 0.05,
    ) -> None:
        self.tsr_drop_threshold = tsr_drop_threshold
        self.latency_increase_ms = latency_increase_ms
        self.hallucination_rate_max = hallucination_rate_max

    def check(
        self,
        baseline: dict[str, Any],
        current: dict[str, Any],
    ) -> tuple[bool, str]:
        """Return (passed, message). passed=False blocks the deploy."""
        problems: list[str] = []

        baseline_tsr = float(baseline.get("task_success_rate", 0.0))
        current_tsr = float(current.get("task_success_rate", 0.0))
        if current_tsr < baseline_tsr - self.tsr_drop_threshold:
            problems.append(
                f"task_success_rate dropped from {baseline_tsr:.3f} to "
                f"{current_tsr:.3f} (max drop: {self.tsr_drop_threshold:.3f})"
            )

        baseline_latency = float(baseline.get("latency_ms", 0))
        current_latency = float(current.get("latency_ms", 0))
        if current_latency > baseline_latency + self.latency_increase_ms:
            problems.append(
                f"latency_ms rose from {baseline_latency:.0f} to "
                f"{current_latency:.0f} (max increase: {self.latency_increase_ms}ms)"
            )

        current_hallucination = float(current.get("hallucination_rate", 0.0))
        if current_hallucination > self.hallucination_rate_max:
            problems.append(
                f"hallucination_rate {current_hallucination:.3f} exceeds "
                f"max {self.hallucination_rate_max:.3f}"
            )

        if problems:
            return False, "; ".join(problems)
        return True, "all gates passed"
