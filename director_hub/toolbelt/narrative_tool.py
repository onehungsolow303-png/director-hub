"""Tool: write to the narrative journal. STUB."""
from __future__ import annotations

from typing import Any

from .base import Tool


class NarrativeTool(Tool):
    name = "narrative_write"
    description = "Append to the narrative journal."

    def call(self, **kwargs: Any) -> dict[str, Any]:
        return {"stub": True}
