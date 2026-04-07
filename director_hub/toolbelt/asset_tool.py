"""Tool: request an asset from Asset Manager. STUB."""
from __future__ import annotations

from typing import Any

from .base import Tool


class AssetTool(Tool):
    name = "asset_request"
    description = "Request an asset from the Asset Manager service."

    def call(self, **kwargs: Any) -> dict[str, Any]:
        return {"stub": True, "message": "AssetTool not yet implemented"}
