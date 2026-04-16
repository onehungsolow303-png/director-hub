"""Read/write helpers for the project_tracker state files.

All files live under `director_hub/state/project_tracker/`, which is
gitignored. If the directory doesn't exist it's created on first write.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STATE_DIR = Path(__file__).resolve().parent.parent.parent / "state" / "project_tracker"


def _ensure_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def write_scratch(snapshot: dict[str, Any]) -> Path:
    """Overwrite the 15-minute scratch file."""
    _ensure_dir()
    path = STATE_DIR / "scratch.json"
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return path


def read_scratch() -> dict[str, Any] | None:
    path = STATE_DIR / "scratch.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_permanent(snapshot: dict[str, Any]) -> Path:
    """Update the hourly permanent snapshot."""
    _ensure_dir()
    path = STATE_DIR / "project_state.json"
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return path


def read_permanent() -> dict[str, Any] | None:
    path = STATE_DIR / "project_state.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def append_history(snapshot: dict[str, Any]) -> Path:
    """Append a snapshot line to the hourly history log."""
    _ensure_dir()
    path = STATE_DIR / "history.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot) + "\n")
    return path


def write_narrative(text: str) -> Path:
    _ensure_dir()
    path = STATE_DIR / "narrative.md"
    path.write_text(text, encoding="utf-8")
    return path


def read_narrative() -> str | None:
    path = STATE_DIR / "narrative.md"
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def permanent_age_hours() -> float:
    """How long since the permanent snapshot was last written. inf if never."""
    path = STATE_DIR / "project_state.json"
    if not path.exists():
        return float("inf")
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    now = datetime.now(tz=UTC)
    return (now - mtime).total_seconds() / 3600.0
