"""memory_recall tool — lets the LLM search its own memories mid-reasoning."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from director_hub.toolbelt.base import Tool

if TYPE_CHECKING:
    from director_hub.memory.manager import MemoryManager

log = logging.getLogger(__name__)


class MemoryTool(Tool):
    name = "memory_recall"
    description = (
        "Search your memories from past sessions. Use when the auto-injected "
        "memory context isn't enough — e.g. to check NPC history, past encounter "
        "outcomes, or player preferences for a specific situation."
    )

    def __init__(self, manager: MemoryManager) -> None:
        self._mgr = manager

    @staticmethod
    def _matches(query: str, text: str) -> bool:
        """Return True if *any* word in *query* appears in *text*."""
        terms = query.lower().split()
        lower = text.lower()
        return any(t in lower for t in terms) if terms else False

    def call(self, **kwargs: Any) -> dict[str, Any]:
        query = kwargs.get("query", "")
        tier = kwargs.get("tier", "all")
        k = kwargs.get("k", 5)

        results: list[dict[str, Any]] = []

        try:
            if tier in ("semantic", "all"):
                facts = self._mgr.semantic.all()
                for key, value in facts.items():
                    if self._matches(query, key) or self._matches(query, str(value)):
                        results.append({"source": "semantic", "key": key, "value": value})

            if tier in ("long_term", "all"):
                matches = self._mgr.long.search(query, k=k)
                for m in matches:
                    results.append(
                        {
                            "source": "long_term",
                            "text": m.get("text", str(m)),
                            "relevance": m.get("relevance", 0.0),
                            "confirmed_count": m.get("metadata", {}).get("confirmed_count", 0)
                            if isinstance(m.get("metadata"), dict)
                            else 0,
                        }
                    )

            if tier in ("episodic", "all"):
                all_events = self._mgr.episodic.all()
                for ev in reversed(all_events[-k * 3 :]):
                    ev_str = json.dumps(ev, default=str)
                    if self._matches(query, ev_str):
                        results.append(
                            {
                                "source": "episodic",
                                "event": ev,
                                "timestamp": ev.get("timestamp", ""),
                            }
                        )

            results = results[:k]

        except Exception:
            log.exception("memory_recall failed")
            return {"ok": False, "error": "memory search failed", "results": []}

        return {"ok": True, "results": results}
