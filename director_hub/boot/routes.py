"""Boot-time deep scan endpoint.

Called by the game at startup BEFORE /session/start.
Performs crash recovery, loads full memory context, returns a memory brief.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

router = APIRouter(tags=["boot"])

# These are set by server.py during lifespan init
_game_store = None
_memory = None


def init(game_store, memory) -> None:  # noqa: ANN001
    """Called by server.py to inject dependencies."""
    global _game_store, _memory  # noqa: PLW0603
    _game_store = game_store
    _memory = memory


class BootRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    player_id: str
    save_data: dict[str, Any] | None = None


class BootResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ok: bool
    scan_elapsed_ms: int
    crashed_sessions: list[dict[str, Any]]
    memory_brief: dict[str, Any]


@router.post("/session/boot", response_model=BootResponse)
def session_boot(req: BootRequest) -> BootResponse:
    """Perform boot-time deep scan for a game session."""
    if _game_store is None or _memory is None:
        raise HTTPException(status_code=503, detail="Boot system not initialized")

    from director_hub.boot.deep_scan import deep_scan

    result = deep_scan(
        game_store=_game_store,
        memory=_memory,
        player_id=req.player_id,
        save_data=req.save_data,
    )
    return BootResponse(**result)
