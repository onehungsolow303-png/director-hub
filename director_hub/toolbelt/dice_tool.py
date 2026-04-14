"""Tool: roll dice / resolve a check.

Real implementation using Python's secrets-backed RNG. Mirrors common
RPG dice notation: NdM (e.g., 1d20, 3d6) plus an optional flat modifier.
The Director uses this when it wants to gate a narrative check on chance
without delegating to the engine.

NOTE: For combat dice that affect the engine's source-of-truth state
(HP, AC, etc.), the Director should NOT use this tool — it should
return stat_effects in the DecisionPayload and let the engine resolve.
This tool is for LLM-side narrative checks only.
"""

from __future__ import annotations

import re
import secrets
from typing import Any

from .base import Tool

_DICE_RE = re.compile(r"^\s*(\d+)\s*[dD]\s*(\d+)\s*([+-]\s*\d+)?\s*$")


def _roll(spec: str) -> tuple[int, list[int], int]:
    """Parse and roll a dice spec like '1d20+5'. Returns (total, rolls, modifier)."""
    m = _DICE_RE.match(spec)
    if not m:
        raise ValueError(f"invalid dice spec: {spec!r} (expected NdM[+/-K])")
    n = int(m.group(1))
    sides = int(m.group(2))
    mod_str = (m.group(3) or "").replace(" ", "")
    modifier = int(mod_str) if mod_str else 0
    if n < 1 or n > 100:
        raise ValueError(f"dice count {n} out of range (1..100)")
    if sides < 2 or sides > 1000:
        raise ValueError(f"dice sides {sides} out of range (2..1000)")
    rolls = [secrets.randbelow(sides) + 1 for _ in range(n)]
    total = sum(rolls) + modifier
    return total, rolls, modifier


class DiceTool(Tool):
    name = "dice_resolve"
    description = (
        "Roll dice via NdM[+/-K] notation. Returns total, individual rolls, "
        "modifier, and a passed flag if a `dc` (difficulty class) is provided."
    )

    def call(self, **kwargs: Any) -> dict[str, Any]:
        spec = kwargs.get("spec", "1d20")
        try:
            total, rolls, modifier = _roll(spec)
        except ValueError as e:
            return {"ok": False, "error": str(e)}

        result: dict[str, Any] = {
            "ok": True,
            "spec": spec,
            "total": total,
            "rolls": rolls,
            "modifier": modifier,
        }

        if "dc" in kwargs:
            try:
                dc = int(kwargs["dc"])
            except (TypeError, ValueError):
                return {"ok": False, "error": f"invalid dc: {kwargs['dc']!r}"}
            result["dc"] = dc
            result["passed"] = total >= dc
        return result
