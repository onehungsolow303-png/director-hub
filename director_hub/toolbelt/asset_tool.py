"""Tool: request an asset from Asset Manager.

Wired to call Asset Manager's HTTP bridge (default 127.0.0.1:7801) via
httpx. Falls back to a structured error when Asset Manager is unreachable
so the reasoning engine never crashes on a transient network error.
"""

from __future__ import annotations

from typing import Any

import httpx

from .base import Tool

DEFAULT_BASE_URL = "http://127.0.0.1:7801"


class AssetTool(Tool):
    name = "asset_request"
    description = "Request an asset from the Asset Manager service."

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def call(self, **kwargs: Any) -> dict[str, Any]:
        kind = kwargs.get("kind", "sprite")
        biome = kwargs.get("biome")
        theme = kwargs.get("theme")
        tags = kwargs.get("tags", [])
        constraints = kwargs.get("constraints", {})
        allow_ai_generation = bool(kwargs.get("allow_ai_generation", False))

        payload = {
            "schema_version": "1.0.0",
            "kind": kind,
            "biome": biome,
            "theme": theme,
            "tags": list(tags),
            "constraints": dict(constraints),
            "allow_ai_generation": allow_ai_generation,
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(f"{self._base_url}/select", json=payload)
        except Exception as e:
            # Boundary: catch any transport-level error and degrade gracefully.
            # Windows wraps connection-refused as httpx.ConnectTimeout (subclass
            # of httpx.RequestError); Linux can surface httpcore.ConnectError
            # directly without httpx wrapping in some httpx/httpcore version
            # combinations. Catching Exception covers both without pinning deps.
            return {
                "ok": False,
                "found": False,
                "error": f"asset manager unreachable: {e}",
            }

        if resp.status_code != 200:
            return {
                "ok": False,
                "found": False,
                "error": f"asset manager returned {resp.status_code}: {resp.text[:200]}",
            }

        body = resp.json()
        return {
            "ok": True,
            "found": body.get("found", False),
            "asset_id": body.get("asset_id"),
            "path": body.get("path"),
            "notes": body.get("notes", []),
        }
