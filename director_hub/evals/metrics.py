"""TSR, ToolAcc, Adherence, Latency, Cost, Autonomy, Recovery, Hallucination. STUB."""

from __future__ import annotations

from typing import Any


class Metrics:
    def task_success_rate(self, results: list[dict[str, Any]]) -> float:
        if not results:
            return 0.0
        return sum(1 for r in results if r.get("success")) / len(results)
