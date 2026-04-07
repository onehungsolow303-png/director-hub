"""Plan generation - breaks high-level player goals into tool-call sequences.

Pure-logic planner (no LLM): pattern-matches the goal string against a
small library of plan templates and emits an ordered list of tool calls.
The reasoning engine can then execute each call (or hand the plan to a
real LLM provider for elaboration).

This is intentionally simple — it covers the common shapes the demo
needs without depending on the LLM provider being configured. Real
LLM-driven planning is the AnthropicProvider's job inside `interpret()`;
this Planner is the deterministic fallback path.
"""
from __future__ import annotations

import re
from typing import Any

# (regex pattern, plan template) — first match wins
_PLAN_TEMPLATES: list[tuple[re.Pattern[str], list[dict[str, Any]]]] = [
    (
        re.compile(r"\battack(s|ing|ed)?\b|\bstrike(s|ing)?\b|\bhit(s|ting)?\b", re.I),
        [
            {"tool": "game_state_read"},
            {"tool": "dice_resolve", "spec": "1d20", "dc": 12},
            {"tool": "narrative_write", "actor": "system", "text": "combat resolution"},
        ],
    ),
    (
        re.compile(r"\bdialogue\b|\bspeak\b|\btalk\b|\bask\b|\bgreet\b", re.I),
        [
            {"tool": "game_state_read"},
            {"tool": "narrative_write", "actor": "npc", "text": "dialogue beat"},
        ],
    ),
    (
        re.compile(r"\bsearch\b|\blook\b|\bexamine\b|\binvestigate\b", re.I),
        [
            {"tool": "game_state_read"},
            {"tool": "dice_resolve", "spec": "1d20", "dc": 10},
            {"tool": "narrative_write", "actor": "system", "text": "perception result"},
        ],
    ),
    (
        re.compile(r"\bequip\b|\bwield\b|\buse\b.*\b(item|potion|spell)\b", re.I),
        [
            {"tool": "asset_request", "kind": "sprite"},
            {"tool": "narrative_write", "actor": "player", "text": "item used"},
        ],
    ),
]

_FALLBACK_PLAN: list[dict[str, Any]] = [
    {"tool": "game_state_read"},
    {"tool": "narrative_write", "actor": "system", "text": "freeform action"},
]


class Planner:
    def plan(self, goal: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Return an ordered list of tool calls that should be executed
        to handle the goal. Each call is a dict with at least a 'tool'
        key naming the toolbelt entry to invoke; additional keys are
        passed as kwargs to that tool.
        """
        for pattern, template in _PLAN_TEMPLATES:
            if pattern.search(goal):
                # Deep-copy each call so callers can mutate freely
                return [dict(call) for call in template]
        return [dict(call) for call in _FALLBACK_PLAN]
