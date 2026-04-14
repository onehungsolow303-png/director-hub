"""Per-request structured logging for the Director Hub bridge.

Complements `Tracer` (which captures per-phase spans inside the
LoopController) by writing one summary line per HTTP /interpret_action,
/dialogue, /quest, /session/start request. Each line is a JSON object
with the fields needed to debug bad responses after the fact:

  {
    "ts":           ISO-8601 timestamp,
    "endpoint":     "/interpret_action" | "/dialogue" | etc,
    "session_id":   the session this request belongs to,
    "actor_id":     the actor field from the request (usually "player"),
    "player_input": the raw input text (truncated to 500 chars),
    "latency_ms":   total time from request receipt to response send,
    "success":      bool from the DecisionPayload,
    "scale":        int 1-10 from the DecisionPayload,
    "fallback":     deterministic_fallback flag,
    "narrative_preview": first 200 chars of narrative_text,
    "stat_effect_count": len(stat_effects),
    "fx_request_count":  len(fx_requests),
  }

Output: append-only JSONL at
  <traces_root>/<YYYY-MM-DD>/requests.jsonl

Best-effort: any I/O failure is logged at WARNING level and the
request itself still succeeds. Logging is never on the critical path.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_TRACES_ROOT = Path("C:/Dev/.shared/traces")
_PLAYER_INPUT_PREVIEW_LEN = 500
_NARRATIVE_PREVIEW_LEN = 200


def log_request(
    endpoint: str,
    request: dict[str, Any],
    response: dict[str, Any],
    latency_ms: int,
    traces_root: Path | None = None,
) -> None:
    """Append a single JSONL summary line for one HTTP request.

    Best-effort: catches all I/O errors so a disk-full or permission
    issue never breaks the request itself. Pre-truncates string fields
    so a runaway player_input or narrative can't blow out the line.
    """
    root = traces_root or DEFAULT_TRACES_ROOT
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    path = root / today / "requests.jsonl"

    player_input = str(request.get("player_input", ""))
    if len(player_input) > _PLAYER_INPUT_PREVIEW_LEN:
        player_input = player_input[:_PLAYER_INPUT_PREVIEW_LEN] + "...[truncated]"

    narrative = str(response.get("narrative_text", ""))
    if len(narrative) > _NARRATIVE_PREVIEW_LEN:
        narrative_preview = narrative[:_NARRATIVE_PREVIEW_LEN] + "..."
    else:
        narrative_preview = narrative

    record = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "endpoint": endpoint,
        "session_id": request.get("session_id"),
        "actor_id": request.get("actor_id"),
        "player_input": player_input,
        "latency_ms": latency_ms,
        "success": response.get("success"),
        "scale": response.get("scale"),
        "fallback": response.get("deterministic_fallback"),
        "narrative_preview": narrative_preview,
        "stat_effect_count": len(response.get("stat_effects") or []),
        "fx_request_count": len(response.get("fx_requests") or []),
    }

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str))
            f.write("\n")
    except OSError as e:
        logger.warning("[request_log] failed to persist %s: %s", endpoint, e)
