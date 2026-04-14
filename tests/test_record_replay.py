"""RecordReplayProvider tests.

Verifies the cassette-based record/replay mechanism that gives the
agentic AI golden-test reproducibility:

  1. live mode is a passthrough (cassette dir is never touched)
  2. record mode calls the backing provider AND writes a cassette
  3. replay mode reads the cassette and never calls the backing provider
  4. replay mode raises CassetteMiss when the request hasn't been recorded
  5. session_id changes do NOT invalidate cassettes (it's stripped from
     the hash because conversation IDs are per-test)
  6. player_input changes DO invalidate cassettes (different request →
     different hash → cassette miss)
  7. ReasoningEngine wires the wrapper from config
  8. ReasoningEngine wires the wrapper from the env var override

The fake backing provider counts every interpret() call, so we can
prove the backing provider is/isn't being invoked under each mode.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from director_hub.reasoning.engine import ReasoningEngine
from director_hub.reasoning.providers.base import ReasoningProvider
from director_hub.reasoning.providers.record_replay import (
    CassetteMiss,
    RecordReplayProvider,
    ReplayMode,
)


class CountingProvider(ReasoningProvider):
    """A backing provider that returns canned responses + counts calls."""

    name = "counting"

    def __init__(self) -> None:
        self.call_count = 0
        self._responses: list[dict[str, Any]] = []

    @property
    def is_real(self) -> bool:
        return True

    def queue_response(self, response: dict[str, Any]) -> None:
        self._responses.append(response)

    def interpret(self, action_request: dict[str, Any]) -> dict[str, Any]:
        self.call_count += 1
        if self._responses:
            return self._responses.pop(0)
        return {
            "success": True,
            "scale": 5,
            "narrative_text": f"counted call {self.call_count}",
            "stat_effects": [],
            "fx_requests": [],
            "repetition_penalty": 0,
        }


def _make_request(
    player_input: str = "I attack the goblin", session_id: str = "test-1"
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "session_id": session_id,
        "actor_id": "player",
        "player_input": player_input,
        "actor_stats": {"hp": 20, "max_hp": 20},
        "scene_context": {"biome": "forest"},
    }


# ─────────────────────────────────────────────────────────────────
# Live mode
# ─────────────────────────────────────────────────────────────────


def test_live_mode_is_passthrough(tmp_path: Path):
    backing = CountingProvider()
    backing.queue_response(
        {
            "success": True,
            "scale": 7,
            "narrative_text": "live response",
            "stat_effects": [],
            "fx_requests": [],
            "repetition_penalty": 0,
        }
    )
    provider = RecordReplayProvider(
        backing=backing,
        mode=ReplayMode.LIVE,
        cassette_dir=tmp_path,
    )
    decision = provider.interpret(_make_request())
    assert decision["narrative_text"] == "live response"
    assert backing.call_count == 1
    # Live mode should not write any cassettes
    assert list(tmp_path.glob("*.json")) == []


# ─────────────────────────────────────────────────────────────────
# Record mode
# ─────────────────────────────────────────────────────────────────


def test_record_mode_calls_backing_and_writes_cassette(tmp_path: Path):
    backing = CountingProvider()
    backing.queue_response(
        {
            "success": True,
            "scale": 6,
            "narrative_text": "recorded response",
            "stat_effects": [],
            "fx_requests": [],
            "repetition_penalty": 0,
        }
    )
    provider = RecordReplayProvider(
        backing=backing,
        mode=ReplayMode.RECORD,
        cassette_dir=tmp_path,
    )

    decision = provider.interpret(_make_request())

    assert decision["narrative_text"] == "recorded response"
    assert backing.call_count == 1

    cassettes = list(tmp_path.glob("*.json"))
    assert len(cassettes) == 1
    cassette_data = json.loads(cassettes[0].read_text(encoding="utf-8"))
    assert cassette_data["response"]["narrative_text"] == "recorded response"
    assert "hash" in cassette_data
    assert "recorded_at" in cassette_data
    # Stripped fields must NOT appear in the cassette's request snapshot
    assert "session_id" not in cassette_data["request"]
    assert "schema_version" not in cassette_data["request"]


def test_record_mode_propagates_backing_exceptions(tmp_path: Path):
    """If the backing provider raises, record mode should not silently
    swallow it — the eval-recording author needs to know capture failed
    so they can fix the underlying issue (e.g., bad credentials)."""

    class BoomProvider(ReasoningProvider):
        name = "boom"

        def interpret(self, _req):
            raise RuntimeError("backing exploded")

    provider = RecordReplayProvider(
        backing=BoomProvider(),
        mode=ReplayMode.RECORD,
        cassette_dir=tmp_path,
    )
    with pytest.raises(RuntimeError, match="backing exploded"):
        provider.interpret(_make_request())
    # Failed recordings must NOT leave a cassette behind
    assert list(tmp_path.glob("*.json")) == []


# ─────────────────────────────────────────────────────────────────
# Replay mode
# ─────────────────────────────────────────────────────────────────


def test_replay_mode_returns_cached_response_without_calling_backing(tmp_path: Path):
    # First, record
    backing = CountingProvider()
    backing.queue_response(
        {
            "success": True,
            "scale": 8,
            "narrative_text": "this is the canned reply",
            "stat_effects": [{"target_id": "player", "stat": "hp", "delta": 3}],
            "fx_requests": [],
            "repetition_penalty": 0,
        }
    )
    recorder = RecordReplayProvider(
        backing=backing,
        mode=ReplayMode.RECORD,
        cassette_dir=tmp_path,
    )
    request = _make_request()
    recorder.interpret(request)
    assert backing.call_count == 1

    # Now replay against a fresh backing (same cassette dir)
    fresh_backing = CountingProvider()
    replayer = RecordReplayProvider(
        backing=fresh_backing,
        mode=ReplayMode.REPLAY,
        cassette_dir=tmp_path,
    )
    decision = replayer.interpret(request)

    assert decision["narrative_text"] == "this is the canned reply"
    assert decision["stat_effects"][0]["delta"] == 3
    # Crucial: the backing provider was NEVER called in replay mode
    assert fresh_backing.call_count == 0


def test_replay_mode_raises_on_cassette_miss(tmp_path: Path):
    fresh_backing = CountingProvider()
    replayer = RecordReplayProvider(
        backing=fresh_backing,
        mode=ReplayMode.REPLAY,
        cassette_dir=tmp_path,
    )
    with pytest.raises(CassetteMiss, match="no cassette"):
        replayer.interpret(_make_request())
    assert fresh_backing.call_count == 0


# ─────────────────────────────────────────────────────────────────
# Hash stability
# ─────────────────────────────────────────────────────────────────


def test_session_id_does_not_affect_hash(tmp_path: Path):
    """Two requests differing only by session_id must hit the same cassette."""
    backing = CountingProvider()
    backing.queue_response(
        {
            "success": True,
            "scale": 5,
            "narrative_text": "stable across sessions",
            "stat_effects": [],
            "fx_requests": [],
            "repetition_penalty": 0,
        }
    )
    recorder = RecordReplayProvider(
        backing=backing,
        mode=ReplayMode.RECORD,
        cassette_dir=tmp_path,
    )
    recorder.interpret(_make_request(session_id="session-A"))
    assert backing.call_count == 1

    fresh_backing = CountingProvider()
    replayer = RecordReplayProvider(
        backing=fresh_backing,
        mode=ReplayMode.REPLAY,
        cassette_dir=tmp_path,
    )
    # Same player_input/scene/actor_stats but a totally different session_id
    decision = replayer.interpret(_make_request(session_id="totally-different-session"))
    assert decision["narrative_text"] == "stable across sessions"
    assert fresh_backing.call_count == 0


def test_player_input_change_invalidates_cassette(tmp_path: Path):
    """Changing the player_input must produce a different hash and miss."""
    backing = CountingProvider()
    backing.queue_response(
        {
            "success": True,
            "scale": 5,
            "narrative_text": "first",
            "stat_effects": [],
            "fx_requests": [],
            "repetition_penalty": 0,
        }
    )
    recorder = RecordReplayProvider(
        backing=backing,
        mode=ReplayMode.RECORD,
        cassette_dir=tmp_path,
    )
    recorder.interpret(_make_request(player_input="I attack the goblin"))

    fresh_backing = CountingProvider()
    replayer = RecordReplayProvider(
        backing=fresh_backing,
        mode=ReplayMode.REPLAY,
        cassette_dir=tmp_path,
    )
    with pytest.raises(CassetteMiss):
        replayer.interpret(_make_request(player_input="I run away from the goblin"))
    assert fresh_backing.call_count == 0


def test_hash_is_order_independent(tmp_path: Path):
    """Dicts assembled in different key orders must hash identically."""
    h1 = RecordReplayProvider._hash_request({"a": 1, "b": 2, "c": {"x": 1, "y": 2}})
    h2 = RecordReplayProvider._hash_request({"c": {"y": 2, "x": 1}, "b": 2, "a": 1})
    assert h1 == h2


# ─────────────────────────────────────────────────────────────────
# ReasoningEngine wiring
# ─────────────────────────────────────────────────────────────────


def test_engine_with_replay_mode_live_does_not_wrap(tmp_path: Path):
    """replay_mode: live (the default) must NOT wrap the provider, so
    production paths pay zero overhead."""
    engine = ReasoningEngine(
        config={
            "active": "stub",
            "providers": [{"name": "stub"}],
            "replay_mode": "live",
            "cassette_dir": str(tmp_path),
        }
    )
    assert engine.provider_name == "stub"  # bare stub, not record_replay


def test_engine_with_replay_mode_record_wraps_provider(tmp_path: Path):
    engine = ReasoningEngine(
        config={
            "active": "stub",
            "providers": [{"name": "stub"}],
            "replay_mode": "record",
            "cassette_dir": str(tmp_path),
        }
    )
    assert engine.provider_name == "record_replay"

    # And running an interpret() through the engine should write a cassette
    engine.interpret(_make_request())
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_engine_env_var_override_wins(monkeypatch, tmp_path: Path):
    """DIRECTOR_HUB_REPLAY_MODE must override the config value so the
    eval runner can flip modes per-invocation without editing models.yaml."""
    monkeypatch.setenv("DIRECTOR_HUB_REPLAY_MODE", "record")
    monkeypatch.setenv("DIRECTOR_HUB_CASSETTE_DIR", str(tmp_path))

    engine = ReasoningEngine(
        config={
            "active": "stub",
            "providers": [{"name": "stub"}],
            "replay_mode": "live",  # config says live, env var says record — env wins
        }
    )
    assert engine.provider_name == "record_replay"
    engine.interpret(_make_request())
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_engine_unknown_replay_mode_falls_back_to_live(tmp_path: Path):
    engine = ReasoningEngine(
        config={
            "active": "stub",
            "providers": [{"name": "stub"}],
            "replay_mode": "make_up_a_mode",
        }
    )
    # Should NOT wrap; should use the bare stub
    assert engine.provider_name == "stub"


def test_engine_propagates_cassette_miss_in_replay_mode(tmp_path: Path):
    """CassetteMiss must surface as a hard failure in replay mode — the
    engine's broad except-Exception fall-back-to-stub path is for
    real LLM failures, not for forgotten cassettes. If we silently fall
    back to the stub on cassette miss, the eval runner sees a 200 with
    a stub response instead of failing loudly, which defeats the entire
    point of golden-test reproducibility."""
    engine = ReasoningEngine(
        config={
            "active": "stub",
            "providers": [{"name": "stub"}],
            "replay_mode": "replay",
            "cassette_dir": str(tmp_path),  # empty dir → every request misses
        }
    )
    with pytest.raises(CassetteMiss):
        engine.interpret(_make_request())
