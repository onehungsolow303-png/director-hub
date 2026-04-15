"""Assemble memory context block for LLM system prompt injection."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from director_hub.memory.manager import MemoryManager

log = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 4


class MemoryRetriever:
    def __init__(self, manager: MemoryManager) -> None:
        self._mgr = manager

    def assemble(
        self,
        action_request: dict[str, Any],
        session_id: str,
        token_budget: int,
    ) -> str:
        """Build the ## Director Memory block for system prompt injection."""
        budget_chars = token_budget * _CHARS_PER_TOKEN
        sections: list[str] = ["## Director Memory\n"]
        used = len(sections[0])

        # 1. Semantic rules (always included)
        rules = self._mgr.semantic.all()
        if rules:
            lines = ["### Rules (things you know to be true)"]
            for key, value in rules.items():
                line = f"- **{key}**: {value}"
                lines.append(line)
            rule_block = "\n".join(lines)
            sections.append(rule_block)
            used += len(rule_block)
        else:
            sections.append("### Rules\nNo rules learned yet.")

        # 2. Long-term journal (vector search, budget-limited)
        remaining = budget_chars - used
        if remaining > 200:
            query = self._build_query(action_request)
            k = min(15, max(3, remaining // 300))
            results = self._mgr.long.search(query, k=k)
            if results:
                lines = ["\n### Past Experience (relevant memories)"]
                for r in results:
                    text = r.get("text", str(r))
                    entry = f"- {text[:300]}"
                    if used + len(entry) > budget_chars:
                        break
                    lines.append(entry)
                    used += len(entry)
                sections.append("\n".join(lines))
            else:
                sections.append("\n### Past Experience\nNo relevant memories found.")

        # 3. Episodic recent (current session, last 5 events)
        remaining = budget_chars - used
        if remaining > 100:
            events = self._mgr.episodic.for_session(session_id)
            recent = events[-5:] if events else []
            if recent:
                lines = ["\n### This Session"]
                for ev in recent:
                    summary = ev.get("type", "event")
                    detail = ev.get("summary", json.dumps(ev, default=str)[:150])
                    entry = f"- {summary}: {detail}"
                    lines.append(entry)
                sections.append("\n".join(lines))

        return "\n".join(sections)

    @staticmethod
    def _build_query(action_request: dict[str, Any]) -> str:
        """Build a search query from the request context."""
        scene = action_request.get("scene_context") or {}
        parts = []
        if scene.get("biome"):
            parts.append(scene["biome"])
        if scene.get("location"):
            parts.append(scene["location"])
        if scene.get("npc_persona"):
            parts.append(scene["npc_persona"])
        actor = action_request.get("actor_stats") or {}
        if actor.get("level"):
            parts.append(f"level {actor['level']}")
        return " ".join(parts) if parts else "game encounter"
