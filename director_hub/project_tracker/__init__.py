"""Continuous project-state tracker.

Scans all four repos (Forever engine, Asset Manager, Director Hub, .shared)
on a 15-minute cadence, writes snapshot to disk, consolidates to a permanent
snapshot every hour. The hourly narrative.md is the primary consumption
surface for Claude Code sessions wanting "where are we right now?" context.

Design spec: `.shared/docs/superpowers/specs/2026-04-16-project-state-tracker-design.md`
"""

from director_hub.project_tracker.loop import start_tracker, stop_tracker
from director_hub.project_tracker.routes import router

__all__ = ["start_tracker", "stop_tracker", "router"]
