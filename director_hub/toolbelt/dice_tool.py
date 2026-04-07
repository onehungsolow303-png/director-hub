"""Tool: ask the engine to resolve a dice/check. STUB."""
from __future__ import annotations

from typing import Any

from .base import Tool


class DiceTool(Tool):
    name = "dice_resolve"
    description = "Ask Forever engine to resolve a dice check using its RPG/ rules."

    def call(self, **kwargs: Any) -> dict[str, Any]:
        return {"stub": True, "rolled": 0, "passed": False}
