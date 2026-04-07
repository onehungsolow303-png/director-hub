"""Full trace capture - input prompt, CoT, tool call, output, decision. STUB."""
from __future__ import annotations

from typing import Any


class Tracer:
    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def record(self, span: dict[str, Any]) -> None:
        self._records.append(span)

    def flush(self) -> list[dict[str, Any]]:
        out = list(self._records)
        self._records.clear()
        return out
