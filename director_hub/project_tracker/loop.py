"""Asyncio scheduler for the ProjectStateTracker.

Runs a scan every 15 minutes. Every hour, promotes the latest scratch to
the permanent snapshot, appends to history, and regenerates the narrative.
Starts via FastAPI startup event; cancelled on shutdown.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from director_hub.project_tracker import narrative_gen, scanner, storage

logger = logging.getLogger(__name__)

SCAN_INTERVAL_SECONDS = 15 * 60
CONSOLIDATION_INTERVAL_HOURS = 1.0

_task: asyncio.Task[None] | None = None
_shutdown = False


async def _scan_once() -> dict[str, Any]:
    """Run a scan in a thread to avoid blocking the event loop on git/disk I/O."""
    return await asyncio.to_thread(scanner.full_scan)


def _consolidate(snapshot: dict[str, Any]) -> None:
    """Promote scratch to permanent, append to history, regenerate narrative."""
    storage.write_permanent(snapshot)
    storage.append_history(snapshot)
    narrative = narrative_gen.render(snapshot)
    storage.write_narrative(narrative)
    logger.info(
        "[project_tracker] hourly consolidation: scanned %d repos, narrative %d chars",
        len(snapshot.get("repos", {})),
        len(narrative),
    )


async def _loop() -> None:
    """Main tracker loop. Scans every 15min, consolidates every hour."""
    global _shutdown
    # Initial scan on startup so /project-state is never empty
    try:
        first = await _scan_once()
        storage.write_scratch(first)
        # Force consolidation on first boot if no permanent snapshot exists yet
        if storage.read_permanent() is None:
            _consolidate(first)
    except Exception as exc:  # noqa: BLE001 — one snapshot failure shouldn't kill the loop
        logger.warning("[project_tracker] initial scan failed: %s", exc)

    while not _shutdown:
        try:
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)
            if _shutdown:
                break
            snapshot = await _scan_once()
            storage.write_scratch(snapshot)
            if storage.permanent_age_hours() >= CONSOLIDATION_INTERVAL_HOURS:
                _consolidate(snapshot)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("[project_tracker] scan cycle failed: %s", exc)


def start_tracker() -> None:
    """Start the tracker loop as a background asyncio task. Safe to call twice."""
    global _task, _shutdown
    if _task is not None and not _task.done():
        return
    _shutdown = False
    _task = asyncio.create_task(_loop(), name="project_tracker")
    logger.info("[project_tracker] started")


async def stop_tracker() -> None:
    """Signal shutdown and await task completion."""
    global _task, _shutdown
    _shutdown = True
    if _task is None:
        return
    _task.cancel()
    try:
        await _task
    except asyncio.CancelledError:
        pass
    finally:
        _task = None
    logger.info("[project_tracker] stopped")


async def force_scan() -> dict[str, Any]:
    """Run an immediate scan + consolidation, bypassing the cadence.
    Used by POST /project-state/force-scan."""
    snapshot = await _scan_once()
    storage.write_scratch(snapshot)
    _consolidate(snapshot)
    return snapshot
