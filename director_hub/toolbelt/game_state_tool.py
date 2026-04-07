"""Tool: read engine state.

Two read paths, in priority order:

1. LIVE: GET http://127.0.0.1:7803/state from Forever engine's
   GameStateServer. Returns the engine's actual current state (player
   HP, hex position, gold, pending encounter/location, session_id,
   etc.). Falls through to the cache if the server is unreachable.

2. CACHED: A session-scoped dict the bridge populates whenever an
   ActionRequest arrives. The most recent (actor_stats, target_stats,
   scene_context) the engine sent. Always available, never stale by
   more than one request.

The live path is the source of truth when both Forever engine and
Director Hub are running locally. The cached path is the safety net
for tests, offline replay, and Director Hub instances that aren't
co-located with a Forever engine.
"""
from __future__ import annotations

from typing import Any

import httpx

from .base import Tool

DEFAULT_STATE_URL = "http://127.0.0.1:7803"

_session_cache: dict[str, dict[str, Any]] = {}


def remember_request(action_request: dict[str, Any]) -> None:
    """Cache the latest action request payload by session id. Called by
    the bridge so the GameStateTool can answer with current engine state
    even when the Forever engine HTTP server is unreachable.
    """
    sid = action_request.get("session_id")
    if not sid:
        return
    _session_cache[sid] = {
        "actor_id": action_request.get("actor_id"),
        "actor_stats": action_request.get("actor_stats", {}),
        "target_id": action_request.get("target_id"),
        "target_stats": action_request.get("target_stats"),
        "scene_context": action_request.get("scene_context", {}),
        "recent_history": action_request.get("recent_history", []),
    }


class GameStateTool(Tool):
    name = "game_state_read"
    description = (
        "Read live engine state from Forever engine's GameStateServer "
        "(http://127.0.0.1:7803/state). Falls back to a session-scoped "
        "cache populated from recent action requests when the server is "
        "unreachable."
    )

    def __init__(self, base_url: str = DEFAULT_STATE_URL, timeout: float = 1.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def call(self, **kwargs: Any) -> dict[str, Any]:
        session_id = kwargs.get("session_id")

        # 1. Try the live endpoint
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(f"{self._base_url}/state")
            if resp.status_code == 200:
                live = resp.json()
                live["source"] = "live"
                return {"ok": True, "found": True, "snapshot": live}
        except httpx.RequestError:
            pass  # fall through to cache

        # 2. Fall back to the cache
        if not session_id:
            return {
                "ok": False,
                "error": "live endpoint unreachable and no session_id given for cache lookup",
            }
        snapshot = _session_cache.get(session_id)
        if snapshot is None:
            return {
                "ok": True,
                "session_id": session_id,
                "found": False,
                "note": "live endpoint unreachable and no cached state for this session",
            }
        return {
            "ok": True,
            "session_id": session_id,
            "found": True,
            "snapshot": {**snapshot, "source": "cache"},
        }
