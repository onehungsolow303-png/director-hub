"""Trace capture with optional disk persistence.

In-memory ring buffer of trace spans the LoopController writes after
each phase. Optionally flushes to JSONL files under `.shared/traces/<date>/`
so the eval replay path can replay real production traces (per spec
'Real Task Replay' best practice).

Each span is a dict with at minimum {trace_id, phase, ts}. The
LoopController adds phase-specific fields (observation_summary,
decision_summary, elapsed_ms, failure_tag).
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_TRACES_ROOT = Path("C:/Dev/.shared/traces")


class Tracer:
    def __init__(
        self,
        max_in_memory: int = 1000,
        traces_root: Path | None = None,
        persist: bool = True,
    ) -> None:
        self._records: list[dict[str, Any]] = []
        self._max_in_memory = max_in_memory
        self._traces_root = traces_root or DEFAULT_TRACES_ROOT
        self._persist = persist

    def record(self, span: dict[str, Any]) -> None:
        self._records.append(span)
        if len(self._records) > self._max_in_memory:
            # Drop the oldest record to bound memory
            self._records.pop(0)
        if self._persist:
            try:
                self._append_to_disk(span)
            except OSError as e:
                logger.warning("[Tracer] failed to persist span: %s", e)

    def flush(self) -> list[dict[str, Any]]:
        """Return and clear the in-memory records.

        Disk persistence is unaffected — flush only manages the in-memory
        buffer. Use this when you want to ship a batch of spans elsewhere
        (e.g., to LangSmith / Arize) without losing on-disk history.
        """
        out = list(self._records)
        self._records.clear()
        return out

    def all(self) -> list[dict[str, Any]]:
        """Read-only view of the in-memory records."""
        return list(self._records)

    def _append_to_disk(self, span: dict[str, Any]) -> None:
        """Append a single span to today's JSONL file under traces_root.

        File path: traces_root/YYYY-MM-DD/spans.jsonl
        """
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        dir_path = self._traces_root / today
        dir_path.mkdir(parents=True, exist_ok=True)
        out_file = dir_path / "spans.jsonl"
        # JSONL: one span per line
        line = json.dumps(span, default=str)
        with out_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def __len__(self) -> int:
        return len(self._records)
