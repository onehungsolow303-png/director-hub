"""Tests for the per-request structured logger.

Verifies the JSONL writer:
  - Creates the date directory under traces_root
  - Appends one line per call (doesn't truncate)
  - Captures all expected fields
  - Truncates over-long player_input and narrative_text
  - Survives I/O errors gracefully (no exception raised to caller)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from director_hub.observability.request_log import log_request


def _request(player_input: str = "I attack the goblin") -> dict:
    return {
        "session_id": "test-session",
        "actor_id": "player",
        "player_input": player_input,
    }


def _response(narrative: str = "The goblin staggers back.") -> dict:
    return {
        "success": True,
        "scale": 6,
        "narrative_text": narrative,
        "stat_effects": [{"target_id": "goblin_1", "stat": "hp", "delta": -4}],
        "fx_requests": [{"kind": "blood_splash"}],
        "deterministic_fallback": False,
    }


def test_log_request_writes_jsonl_line(tmp_path: Path):
    log_request("/interpret_action", _request(), _response(), latency_ms=42, traces_root=tmp_path)

    files = list(tmp_path.rglob("requests.jsonl"))
    assert len(files) == 1, "expected exactly one requests.jsonl"

    lines = files[0].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["endpoint"] == "/interpret_action"
    assert record["session_id"] == "test-session"
    assert record["actor_id"] == "player"
    assert record["player_input"] == "I attack the goblin"
    assert record["latency_ms"] == 42
    assert record["success"] is True
    assert record["scale"] == 6
    assert record["fallback"] is False
    assert record["narrative_preview"] == "The goblin staggers back."
    assert record["stat_effect_count"] == 1
    assert record["fx_request_count"] == 1


def test_log_request_appends_multiple_lines(tmp_path: Path):
    for i in range(5):
        log_request(
            "/interpret_action",
            _request(f"action {i}"),
            _response(f"narrative {i}"),
            latency_ms=i * 10,
            traces_root=tmp_path,
        )

    files = list(tmp_path.rglob("requests.jsonl"))
    assert len(files) == 1
    lines = files[0].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 5
    for i, line in enumerate(lines):
        record = json.loads(line)
        assert record["player_input"] == f"action {i}"
        assert record["narrative_preview"] == f"narrative {i}"
        assert record["latency_ms"] == i * 10


def test_log_request_truncates_long_player_input(tmp_path: Path):
    long_input = "x" * 1000
    log_request("/dialogue", _request(long_input), _response(), latency_ms=0, traces_root=tmp_path)

    files = list(tmp_path.rglob("requests.jsonl"))
    record = json.loads(files[0].read_text(encoding="utf-8").splitlines()[0])
    assert "[truncated]" in record["player_input"]
    assert len(record["player_input"]) < len(long_input)


def test_log_request_truncates_long_narrative(tmp_path: Path):
    long_narrative = "y" * 1000
    log_request(
        "/interpret_action",
        _request(),
        _response(long_narrative),
        latency_ms=0,
        traces_root=tmp_path,
    )

    files = list(tmp_path.rglob("requests.jsonl"))
    record = json.loads(files[0].read_text(encoding="utf-8").splitlines()[0])
    assert record["narrative_preview"].endswith("...")
    assert len(record["narrative_preview"]) < len(long_narrative)


def test_log_request_swallows_io_errors(tmp_path: Path):
    """A disk-full or permission error must NOT propagate to the caller."""
    bad_root = tmp_path / "nope"  # we'll patch open to raise

    with patch(
        "director_hub.observability.request_log.Path.open", side_effect=OSError("disk full")
    ):
        # Should not raise
        log_request(
            "/interpret_action", _request(), _response(), latency_ms=10, traces_root=bad_root
        )


def test_log_request_endpoint_field_round_trips(tmp_path: Path):
    for endpoint in ("/interpret_action", "/dialogue", "/quest", "/session/start"):
        log_request(endpoint, _request(), _response(), latency_ms=1, traces_root=tmp_path)

    files = list(tmp_path.rglob("requests.jsonl"))
    lines = files[0].read_text(encoding="utf-8").splitlines()
    endpoints = [json.loads(line)["endpoint"] for line in lines]
    assert endpoints == ["/interpret_action", "/dialogue", "/quest", "/session/start"]
