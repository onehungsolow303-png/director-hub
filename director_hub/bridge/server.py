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

import uuid

from fastapi import FastAPI

from director_hub import __version__
from director_hub.bridge.schemas import (
    ActionRequest,
    DecisionPayload,
    SessionStartRequest,
    SessionStartResponse,
)
from director_hub.reasoning.engine import ReasoningEngine
from director_hub.toolbelt.game_state_tool import remember_request

app = FastAPI(title="Director Hub", version=__version__)
_engine = ReasoningEngine()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "director_hub", "version": __version__}


@app.post("/session/start", response_model=SessionStartResponse)
def session_start(req: SessionStartRequest) -> SessionStartResponse:
    sid = str(uuid.uuid4())
    opening = DecisionPayload(
        session_id=sid,
        success=True,
        scale=5,
        narrative_text="[stub] Welcome to the game. The reasoning engine is not yet wired up.",
        deterministic_fallback=True,
    )
    return SessionStartResponse(session_id=sid, opening=opening)


@app.post("/interpret_action", response_model=DecisionPayload)
def interpret_action(req: ActionRequest) -> DecisionPayload:
    payload = req.model_dump()
    # Populate the GameStateTool cache so a downstream LLM can read the
    # latest engine state via game_state_read even if Forever engine's
    # GameStateServer is unreachable. AnthropicProvider also calls this
    # internally; doing it here too means the stub provider populates
    # the cache (useful for tests + offline replay).
    remember_request(payload)
    result = _engine.interpret(payload)
    return DecisionPayload(**result)


@app.post("/dialogue", response_model=DecisionPayload)
def dialogue(req: ActionRequest) -> DecisionPayload:
    payload = req.model_dump()
    remember_request(payload)
    result = _engine.interpret(payload)
    return DecisionPayload(**result)


@app.post("/quest", response_model=DecisionPayload)
def quest(req: ActionRequest) -> DecisionPayload:
    payload = req.model_dump()
    remember_request(payload)
    result = _engine.interpret(payload)
    return DecisionPayload(**result)
