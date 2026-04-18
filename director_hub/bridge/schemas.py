"""Pydantic models for the Director Hub HTTP bridge.

The schema-backed classes (`ActionRequest`, `DecisionPayload`) are imported
from the generated module that mirrors `C:/Dev/.shared/schemas/`. The two
session lifecycle wrappers (`SessionStartRequest`, `SessionStartResponse`)
are Director Hub-internal — they have no entry in `.shared/schemas/` because
no other service consumes them — so they stay hand-written here.

Hardening for the schema-backed classes (extra="forbid", Literal const
pinning) is applied centrally by `.shared/codegen/python_gen.py`. Hardening
for the local wrappers is applied here for consistency.

Update flow when contracts change:
  1. Edit the JSON schema in C:/Dev/.shared/schemas/
  2. cd C:/Dev/.shared && python codegen/python_gen.py --out codegen/golden_python.py
  3. cp C:/Dev/.shared/codegen/golden_python.py C:/Dev/Director Hub/director_hub/bridge/_generated_schemas.py
  4. Run pytest tests/
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

# Re-export the schema-backed classes under the names callers already use.
# These are the SOURCE OF TRUTH — never redefine them locally.
from director_hub.bridge._generated_schemas import (  # noqa: F401
    ActionRequest,
    DecisionPayload,
)


class SessionStartRequest(BaseModel):
    """Director Hub-internal: opens a new session.

    Not in .shared/schemas/ because no other service produces or consumes
    this exact shape — it's the local handshake at /session/start.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    player_id: str = "player_1"
    player_profile: dict[str, Any]
    map_meta: dict[str, Any]


class SessionStartResponse(BaseModel):
    """Director Hub-internal: response to /session/start."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    session_id: str
    opening: DecisionPayload


class ChunkGenerateRequest(BaseModel):
    """Request for /chunk/generate — chunk metadata sent by the engine."""

    model_config = ConfigDict(extra="forbid")

    chunk_x: int
    chunk_z: int
    biome: str
    elevation: float = 0.5
    temperature: float = 0.5
    moisture: float = 0.5
    distance_from_spawn: int = 0
    world_seed: int = 42


class ChunkGenerateResponse(BaseModel):
    """Response from /chunk/generate — content placed in the chunk."""

    structures: list[dict[str, Any]] = []
    npcs: list[dict[str, Any]] = []
    encounter_zones: list[dict[str, Any]] = []
    points_of_interest: list[dict[str, Any]] = []
    content_source: str = "director_hub"
