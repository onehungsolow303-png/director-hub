"""Tool: append entries to the narrative journal.

Maintains an in-process journal that the Director can write to and read
from across a session. Each entry is a (timestamp, actor, text) tuple.
Real persistence is the EpisodicMemory's job (Round M); this tool just
captures structured journal lines for use within a single reasoning loop.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .base import Tool


class NarrativeTool(Tool):
    name = "narrative_write"
    description = "Append a structured narrative line to the in-session journal."

    def __init__(self) -> None:
        self._journal: list[dict[str, Any]] = []

    def call(self, **kwargs: Any) -> dict[str, Any]:
        action = kwargs.get("action", "append")
        if action == "append":
            text = kwargs.get("text", "")
            actor = kwargs.get("actor", "system")
            entry = {
                "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                "actor": actor,
                "text": text,
            }
            self._journal.append(entry)
            return {"ok": True, "appended": entry, "size": len(self._journal)}

        if action == "read":
            n = int(kwargs.get("n", 10))
            return {"ok": True, "entries": self._journal[-n:], "size": len(self._journal)}

        if action == "clear":
            self._journal.clear()
            return {"ok": True, "cleared": True, "size": 0}

        return {"ok": False, "error": f"unknown action: {action!r}"}
