"""Per-step trace capture. STUB."""
from __future__ import annotations

from typing import Any


class TraceCapture:
    def __init__(self) -> None:
        self._steps: list[dict[str, Any]] = []

    def add(self, step: dict[str, Any]) -> None:
        self._steps.append(step)

    def export(self) -> list[dict[str, Any]]:
        return list(self._steps)
