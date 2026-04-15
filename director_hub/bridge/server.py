"""Director Hub HTTP bridge - FastAPI app on port 7802.

Endpoints (Phase 1 stubs):
    GET  /health             liveness check
    POST /session/start      open a session, return opening narrative
    POST /interpret_action   the core per-decision call
    POST /dialogue           NPC dialogue generation
    POST /quest              dynamic quest generation

Reasoning engine and tools are stubs. Real implementation tracked in
spec §14 follow-ups.
"""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI

from director_hub import __version__
from director_hub.bridge.schemas import (
    ActionRequest,
    DecisionPayload,
    SessionStartRequest,
    SessionStartResponse,
)
from director_hub.content.template_store import TemplateStore
from director_hub.memory.manager import MemoryManager
from director_hub.observability.request_log import log_request
from director_hub.reasoning.engine import ReasoningEngine
from director_hub.reasoning.prediction import PredictionRecorder
from director_hub.reasoning.reflector import InlineReflector
from director_hub.reasoning.session_review import SessionReviewer
from director_hub.toolbelt.game_state_tool import remember_request

app = FastAPI(title="Director Hub", version=__version__)
_memory = MemoryManager(persist=True)
_engine = ReasoningEngine(memory_manager=_memory)
_predictions = PredictionRecorder()
_reflector = InlineReflector(_memory)
_session_reviewer = SessionReviewer(_memory)
_template_store = TemplateStore(memory=_memory)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "director_hub", "version": __version__}


@app.post("/session/start", response_model=SessionStartResponse)
def session_start(req: SessionStartRequest) -> SessionStartResponse:
    sid = str(uuid.uuid4())
    # Explicit defaults for the optional list/int fields. The pydantic
    # generated_schemas defaults them to None, which serializes as JSON
    # null, which C# Newtonsoft cannot deserialize into a non-nullable
    # int / List<T>. The Forever engine GameManager.StartDirectorSession
    # was silently failing on this null and falling back to "no-session"
    # for every session, which broke memory anchoring + NPC continuity.
    # See engine commit f460cd1 for the C# side.
    opening = DecisionPayload(
        session_id=sid,
        success=True,
        scale=5,
        narrative_text="[stub] Welcome to the game. The reasoning engine is not yet wired up.",
        stat_effects=[],
        fx_requests=[],
        repetition_penalty=0,
        deterministic_fallback=True,
    )
    return SessionStartResponse(session_id=sid, opening=opening)


def _interpret_with_logging(endpoint: str, req: ActionRequest) -> DecisionPayload:
    """Shared body for /interpret_action, /dialogue, /quest.

    All three endpoints take an ActionRequest, run it through the
    reasoning engine, and emit a structured per-request log line so
    bad responses can be debugged after the fact (see
    observability/request_log.py for the schema).

    Also handles prediction recording and outcome comparison for the
    memory-driven learning pipeline.
    """
    from director_hub.reasoning.outcome import OutcomeData, compare_outcome

    payload = req.model_dump()
    remember_request(payload)

    session_id = payload.get("session_id", "default")

    party = payload.get("party") or []
    primary_player_id = party[0]["player_id"] if party else payload.get("actor_id", "player")  # noqa: F841 — wired in Task 5

    # Compare previous prediction against this request's outcome
    prev_prediction = _predictions.get_latest(session_id)
    if prev_prediction:
        actor = payload.get("actor_stats") or {}
        max_hp = max(actor.get("max_hp", 1), 1)
        hp_pct = actor.get("hp", max_hp) / max_hp
        party_outcomes = {}
        for pm in party:
            pid = pm.get("player_id", "")
            pm_max = max(pm.get("max_hp", 1), 1)
            party_outcomes[pid] = {"hp_pct_after": pm.get("hp", pm_max) / pm_max}
        outcome = OutcomeData(player_hp_pct_after=hp_pct, party_outcomes=party_outcomes)
        comparison = compare_outcome(prev_prediction, outcome)
        if comparison.should_store:
            _reflector.reflect(
                comparison,
                decision_summary=str(prev_prediction.context_snapshot),
                use_llm=False,
            )

    t0 = time.monotonic()
    result = _engine.interpret(payload)
    latency_ms = (time.monotonic() - t0) * 1000

    # Extract and store prediction
    decision_id = str(uuid.uuid4())
    pred = PredictionRecorder.extract_from_response(result, session_id, decision_id)
    if pred:
        _predictions.record(pred)
    result = PredictionRecorder.strip_from_response(result)

    log_request(endpoint, payload, result, latency_ms)
    return DecisionPayload(**result)


@app.post("/interpret_action", response_model=DecisionPayload)
def interpret_action(req: ActionRequest) -> DecisionPayload:
    return _interpret_with_logging("/interpret_action", req)


@app.post("/dialogue", response_model=DecisionPayload)
def dialogue(req: ActionRequest) -> DecisionPayload:
    return _interpret_with_logging("/dialogue", req)


@app.post("/quest", response_model=DecisionPayload)
def quest(req: ActionRequest) -> DecisionPayload:
    return _interpret_with_logging("/quest", req)


@app.post("/session/end")
def session_end(req: dict) -> dict:
    """Trigger deep session review on save/quit."""
    session_id = req.get("session_id", "default")
    result = _session_reviewer.review(session_id=session_id, use_llm=False)
    return result
