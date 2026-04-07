"""Real-task replay from .shared/traces/. STUB."""
from __future__ import annotations

from pathlib import Path


class TraceReplayer:
    def __init__(self, traces_dir: Path) -> None:
        self.traces_dir = traces_dir

    def list_traces(self) -> list[Path]:
        if not self.traces_dir.exists():
            return []
        return sorted(self.traces_dir.glob("*.json"))
