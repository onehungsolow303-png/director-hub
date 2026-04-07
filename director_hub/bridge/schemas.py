"""Pydantic models matching .shared/schemas/.

Hand-written for Phase 1 to avoid import-path coupling to .shared/codegen.
The goldens in .shared/codegen/golden_python.py are the contract; these
models follow that contract field-for-field.

Phase 1 hardening (post-review fixes 1+2):
- All models pin extra="forbid" to mirror additionalProperties:false in
  the JSON schemas (rejects unknown fields with HTTP 422 instead of
  silently swallowing them).
- schema_version is Literal["1.0.0"] to mirror the JSON schema const
  (rejects version mismatches at the boundary instead of accepting and
  silently re-emitting "1.0.0").

Numeric/length constraints (Field(ge=, le=, min_length=, max_length=))
and nested ActorStats class are deferred to a follow-up; the runtime
jsonschema.validate() against .shared/schemas/ remains the source of
truth per spec §7.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    session_id: str
    actor_id: str
    target_id: Optional[str] = None
    player_input: str
    actor_stats: dict[str, Any]
    target_stats: Optional[dict[str, Any]] = None
    scene_context: Optional[dict[str, Any]] = None
    recent_history: Optional[list[str]] = None


class StatEffect(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_id: str
    stat: str
    delta: int
    status_effect: Optional[str] = None


class FxRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    biome: Optional[str] = None
    theme: Optional[str] = None


class DecisionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    session_id: str
    success: bool
    scale: int
    narrative_text: str
    stat_effects: list[StatEffect] = Field(default_factory=list)
    fx_requests: list[FxRequest] = Field(default_factory=list)
    repetition_penalty: int = 0
    deterministic_fallback: bool = False


class SessionStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    player_profile: dict[str, Any]
    map_meta: dict[str, Any]


class SessionStartResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    session_id: str
    opening: DecisionPayload
