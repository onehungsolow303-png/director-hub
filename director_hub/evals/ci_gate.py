"""CI gate: blocks deploy if metrics regress past threshold. STUB."""
from __future__ import annotations


class CIGate:
    tsr_drop_threshold = 0.05  # 5%
    latency_increase_ms = 100

    def check(self, baseline: dict, current: dict) -> tuple[bool, str]:
        return True, "stub: always passes"
