"""Tool: read engine state. STUB."""
from __future__ import annotations

from typing import Any

from .base import Tool


class GameStateTool(Tool):
    name = "game_state_read"
    description = "Read current engine state (HP, location, inventory, etc.)."

    def call(self, **kwargs: Any) -> dict[str, Any]:
        return {"stub": True}
