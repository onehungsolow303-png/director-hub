"""LoopController + Tracer tests.

Exercises the four-phase loop end-to-end against the stub reasoning engine,
plus the tracer's in-memory + disk-persistence paths.
"""

from __future__ import annotations

import json
from pathlib import Path

from director_hub.loop.controller import LoopController
from director_hub.observability.tracer import Tracer
from director_hub.reasoning.engine import ReasoningEngine


def _observation() -> dict:
    return {
        "schema_version": "1.0.0",
        "session_id": "loop-test",
        "actor_id": "player",
        "player_input": "I attack the goblin",
        "actor_stats": {"hp": 20, "max_hp": 20},
    }


# ---------------------------------------------------------------- LoopController


def test_loop_runs_one_step_against_stub(tmp_path: Path):
    tracer = Tracer(traces_root=tmp_path / "traces")
    loop = LoopController(
        engine=ReasoningEngine(config={"active": "stub", "providers": [{"name": "stub"}]}),
        tracer=tracer,
    )
    decision = loop.step(_observation())
    assert decision["session_id"] == "loop-test"
    assert "narrative_text" in decision
    assert "_trace_id" in decision
    assert decision["deterministic_fallback"] is True


def test_loop_emits_three_trace_phases(tmp_path: Path):
    tracer = Tracer(traces_root=tmp_path / "traces")
    loop = LoopController(
        engine=ReasoningEngine(config={"active": "stub", "providers": [{"name": "stub"}]}),
        tracer=tracer,
    )
    loop.step(_observation())
    spans = tracer.all()
    phases = [s["phase"] for s in spans]
    assert "observe" in phases
    assert "reason+act" in phases
    assert "reflect" in phases


def test_loop_traces_share_a_single_trace_id(tmp_path: Path):
    tracer = Tracer(traces_root=tmp_path / "traces")
    loop = LoopController(
        engine=ReasoningEngine(config={"active": "stub", "providers": [{"name": "stub"}]}),
        tracer=tracer,
    )
    loop.step(_observation())
    spans = tracer.all()
    trace_ids = {s["trace_id"] for s in spans}
    assert len(trace_ids) == 1


def test_loop_handles_engine_failure_gracefully(tmp_path: Path):
    """If the engine raises, the loop catches and emits a fallback decision."""

    class _BoomEngine:
        provider_name = "boom"
        provider_is_real = True

        def interpret(self, _):
            raise RuntimeError("simulated failure")

    tracer = Tracer(traces_root=tmp_path / "traces")
    loop = LoopController(engine=_BoomEngine(), tracer=tracer)
    decision = loop.step(_observation())
    assert decision["success"] is False
    assert "reasoning failed" in decision["narrative_text"]


# ---------------------------------------------------------------- Tracer


def test_tracer_in_memory_record_and_flush(tmp_path: Path):
    tracer = Tracer(traces_root=tmp_path / "traces", persist=False)
    tracer.record({"trace_id": "x", "phase": "observe", "ts": 1.0})
    tracer.record({"trace_id": "x", "phase": "reflect", "ts": 1.1})
    assert len(tracer) == 2
    flushed = tracer.flush()
    assert len(flushed) == 2
    assert len(tracer) == 0


def test_tracer_persists_to_disk(tmp_path: Path):
    traces_root = tmp_path / "traces"
    tracer = Tracer(traces_root=traces_root, persist=True)
    tracer.record({"trace_id": "y", "phase": "observe", "ts": 1.0, "extra": "data"})

    # Find the JSONL file under today's date dir
    files = list(traces_root.rglob("spans.jsonl"))
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8").strip().splitlines()
    assert len(content) == 1
    parsed = json.loads(content[0])
    assert parsed["trace_id"] == "y"
    assert parsed["extra"] == "data"


def test_tracer_in_memory_buffer_is_bounded(tmp_path: Path):
    tracer = Tracer(traces_root=tmp_path / "traces", max_in_memory=5, persist=False)
    for i in range(20):
        tracer.record({"trace_id": str(i), "phase": "observe", "ts": float(i)})
    assert len(tracer) == 5
    # The 5 retained should be the LAST 5 (oldest dropped)
    retained_ids = [s["trace_id"] for s in tracer.all()]
    assert retained_ids == ["15", "16", "17", "18", "19"]
