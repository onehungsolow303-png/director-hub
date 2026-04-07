"""Pydantic models matching .shared/schemas/.

Hand-written for Phase 1 to avoid import-path coupling to .shared/codegen.
The goldens in .shared/codegen/golden_python.py are the contract; these
models follow that contract field-for-field.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ActionRequest(BaseModel):
    schema_version: str = Field(default="1.0.0")
    session_id: str
    actor_id: str
    target_id: Optional[str] = None
    player_input: str
    actor_stats: dict[str, Any]
    target_stats: Optional[dict[str, Any]] = None
    scene_context: Optional[dict[str, Any]] = None
    recent_history: Optional[list[str]] = None


class StatEffect(BaseModel):
    target_id: str
    stat: str
    delta: int
    status_effect: Optional[str] = None


class FxRequest(BaseModel):
    kind: str
    biome: Optional[str] = None
    theme: Optional[str] = None


class DecisionPayload(BaseModel):
    schema_version: str = Field(default="1.0.0")
    session_id: str
    success: bool
    scale: int
    narrative_text: str
    stat_effects: list[StatEffect] = Field(default_factory=list)
    fx_requests: list[FxRequest] = Field(default_factory=list)
    repetition_penalty: int = 0
    deterministic_fallback: bool = False


class SessionStartRequest(BaseModel):
    schema_version: str = Field(default="1.0.0")
    player_profile: dict[str, Any]
    map_meta: dict[str, Any]


class SessionStartResponse(BaseModel):
    schema_version: str = Field(default="1.0.0")
    session_id: str
    opening: DecisionPayload
