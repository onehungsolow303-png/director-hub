"""FastAPI routes for the ProjectStateTracker.

All endpoints are read-only except force-scan. Serving static files
written by the scheduler — the route layer does not do work itself
(except for force_scan which triggers a scan on demand).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from director_hub.project_tracker import loop, storage

router = APIRouter(prefix="/project-state", tags=["project-state"])


@router.get("")
def get_permanent() -> dict:
    """Return the current hourly permanent snapshot."""
    snap = storage.read_permanent()
    if snap is None:
        raise HTTPException(
            status_code=503, detail="no permanent snapshot yet — tracker still booting"
        )
    return snap


@router.get("/scratch")
def get_scratch() -> dict:
    """Return the latest 15-minute scratch snapshot (may be newer than permanent)."""
    snap = storage.read_scratch()
    if snap is None:
        raise HTTPException(
            status_code=503, detail="no scratch snapshot yet — tracker still booting"
        )
    return snap


@router.get("/narrative", response_class=PlainTextResponse)
def get_narrative() -> str:
    """Return the markdown narrative. This is the primary interface for
    new Claude Code sessions wanting a 'where are we' brief."""
    text = storage.read_narrative()
    if text is None:
        raise HTTPException(status_code=503, detail="no narrative yet — tracker still booting")
    return text


@router.post("/force-scan")
async def force_scan() -> dict:
    """Trigger an immediate scan + consolidation, bypass the 15-min cadence."""
    snap = await loop.force_scan()
    return {
        "ok": True,
        "generated_at": snap.get("generated_at"),
        "scan_elapsed_ms": snap.get("scan_elapsed_ms"),
    }
