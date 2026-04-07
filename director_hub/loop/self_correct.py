"""Self-correction: re-plan on tool failure or low-confidence result. STUB."""
from __future__ import annotations

from typing import Any


class SelfCorrector:
    max_replans = 3

    def should_replan(self, result: dict[str, Any]) -> bool:
        return False
