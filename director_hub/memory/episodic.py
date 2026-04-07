"""Episodic memory - what happened in this run.

Disk-backed JSONL log of events. Each event is a dict the caller chooses
the shape of. The Director typically writes a record per LoopController
step (one per player action). On read, events are filtered by session_id
and optional time range.

Persistence is JSONL (one event per line) at
`C:/Dev/.shared/state/episodic/<session_id>.jsonl` by default. The path
is configurable; pass `persist=False` to keep memory in-process only
(useful for tests).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_EPISODIC_ROOT = Path("C:/Dev/.shared/state/episodic")


class EpisodicMemory:
    def __init__(
        self,
        root: Path | None = None,
        persist: bool = True,
    ) -> None:
        self._events: list[dict[str, Any]] = []
        self._root = root or DEFAULT_EPISODIC_ROOT
        self._persist = persist
        if self._persist:
            try:
                self._root.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.warning("[EpisodicMemory] cannot create %s: %s", self._root, e)
                self._persist = False

    def record(self, event: dict[str, Any]) -> None:
        if "timestamp" not in event:
            event = dict(event)
            event["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._events.append(event)
        if self._persist:
            session_id = str(event.get("session_id", "no-session"))
            try:
                self._append_to_disk(session_id, event)
            except OSError as e:
                logger.warning("[EpisodicMemory] persist failed for %s: %s", session_id, e)

    def all(self) -> list[dict[str, Any]]:
        return list(self._events)

    def for_session(self, session_id: str) -> list[dict[str, Any]]:
        """Return all in-memory events for the given session_id, plus any
        on-disk events from previous Director Hub runs that haven't been
        loaded yet.
        """
        in_memory = [e for e in self._events if e.get("session_id") == session_id]
        if not self._persist:
            return in_memory
        on_disk = self._read_from_disk(session_id)
        # De-dupe by serialized form (cheap and order-preserving)
        seen: set[str] = set()
        merged: list[dict[str, Any]] = []
        for e in on_disk + in_memory:
            key = json.dumps(e, sort_keys=True, default=str)
            if key in seen:
                continue
            seen.add(key)
            merged.append(e)
        return merged

    def clear(self) -> None:
        """Clear in-memory events. Disk persistence is unaffected — use
        wipe() to also delete the on-disk JSONL files."""
        self._events.clear()

    def wipe(self) -> None:
        """Delete all in-memory and on-disk events. Use with care."""
        self._events.clear()
        if self._persist and self._root.exists():
            for f in self._root.glob("*.jsonl"):
                f.unlink()

    def _append_to_disk(self, session_id: str, event: dict[str, Any]) -> None:
        out = self._root / f"{session_id}.jsonl"
        line = json.dumps(event, default=str)
        with out.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _read_from_disk(self, session_id: str) -> list[dict[str, Any]]:
        out = self._root / f"{session_id}.jsonl"
        if not out.exists():
            return []
        events: list[dict[str, Any]] = []
        with out.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("[EpisodicMemory] skipping bad line in %s", out)
        return events
