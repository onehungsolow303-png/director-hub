"""Tool: read engine state.

Engine state lives on the Forever engine side and isn't yet proxied to
Director Hub via a dedicated read endpoint. For now this tool reads
from a session-scoped state cache that the bridge updates whenever an
ActionRequest arrives. The cache is the most recent (actor_stats,
target_stats, scene_context) the engine sent — enough for the reasoning
engine to answer 'what is the player's HP right now?' without a
round-trip.

A real implementation would add a /game_state endpoint on Forever
engine and call it via httpx, but that requires Forever engine to
expose state over HTTP, which is a separate spec.
"""
from __future__ import annotations

from typing import Any

from .base import Tool

_session_cache: dict[str, dict[str, Any]] = {}


def remember_request(action_request: dict[str, Any]) -> None:
    """Cache the latest action request payload by session id. Called by
    the bridge so the GameStateTool can answer with current engine state.
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
        "Read the most recent engine state for a session: actor stats, "
        "target stats, scene context, recent history."
    )

    def call(self, **kwargs: Any) -> dict[str, Any]:
        session_id = kwargs.get("session_id")
        if not session_id:
            return {"ok": False, "error": "session_id is required"}
        snapshot = _session_cache.get(session_id)
        if snapshot is None:
            return {
                "ok": True,
                "session_id": session_id,
                "found": False,
                "note": "no state cached yet for this session",
            }
        return {
            "ok": True,
            "session_id": session_id,
            "found": True,
            "snapshot": snapshot,
        }
