"""Tool: emit an atmospherics directive on the next DecisionPayload.

The Director Hub uses this when narrative calls for environmental change
("storm at midnight as the dragon arrives"). The actual visual change
happens client-side via Forever engine's GaiaRuntimeBridge → Gaia's API.

NOTE: This tool only DESCRIBES the atmospherics; it does not directly call
the engine. The orchestrator merges the result into the next DecisionPayload
under `atmospherics`. The engine reads it, applies via GaiaRuntimeBridge.

Field shape mirrors `.shared/schemas/decision.schema.json` properties.atmospherics.
Wind direction is normalized 0-1 (NOT degrees) per Gaia.GaiaAPI convention —
mapping: 0.0 = north (+Z), 0.25 = east, 0.5 = south, 0.75 = west.

Time-of-day → sun mapping (when PW Sky isn't installed):
  Dawn   (06:00) → pitch  10°, rotation  90° (E-rising)
  Noon   (12:00) → pitch -90° (overhead)
  Dusk   (18:00) → pitch  10°, rotation 270° (W-setting)
  Night  (00:00) → pitch  60° (under horizon)
"""

from __future__ import annotations

from typing import Any

from .base import Tool

# Time-of-day presets (engine sees these immediately on apply)
PRESETS_TOD = {
    "dawn": {
        "sun_pitch_deg": 10.0,
        "sun_rotation_deg": 90.0,
        "sun_intensity": 0.6,
        "sun_color_kelvin": 3200,
        "skybox_exposure": 0.8,
        "skybox_tint_rgb": [1.0, 0.85, 0.7],
    },
    "morning": {
        "sun_pitch_deg": -30.0,
        "sun_rotation_deg": 110.0,
        "sun_intensity": 1.0,
        "sun_color_kelvin": 5000,
        "skybox_exposure": 1.0,
        "skybox_tint_rgb": [1.0, 0.97, 0.92],
    },
    "noon": {
        "sun_pitch_deg": -85.0,
        "sun_rotation_deg": 180.0,
        "sun_intensity": 1.2,
        "sun_color_kelvin": 6500,
        "skybox_exposure": 1.2,
        "skybox_tint_rgb": [1.0, 1.0, 1.0],
    },
    "afternoon": {
        "sun_pitch_deg": -45.0,
        "sun_rotation_deg": 230.0,
        "sun_intensity": 1.0,
        "sun_color_kelvin": 5500,
        "skybox_exposure": 1.0,
        "skybox_tint_rgb": [1.0, 0.95, 0.85],
    },
    "dusk": {
        "sun_pitch_deg": 10.0,
        "sun_rotation_deg": 270.0,
        "sun_intensity": 0.5,
        "sun_color_kelvin": 2800,
        "skybox_exposure": 0.7,
        "skybox_tint_rgb": [1.0, 0.7, 0.5],
    },
    "night": {
        "sun_pitch_deg": 60.0,
        "sun_rotation_deg": 0.0,
        "sun_intensity": 0.1,
        "sun_color_kelvin": 8000,
        "skybox_exposure": 0.2,
        "skybox_tint_rgb": [0.3, 0.4, 0.7],
    },
}

# Weather presets (apply on top of TOD — modify wind + tint)
PRESETS_WEATHER = {
    "calm": {"wind_speed": 0.05, "wind_direction_norm": 0.5},
    "breezy": {"wind_speed": 0.30, "wind_direction_norm": 0.5},
    "stormy": {
        "wind_speed": 1.00,
        "wind_direction_norm": 0.5,
        "skybox_exposure": 0.4,
        "skybox_tint_rgb": [0.5, 0.5, 0.6],
    },
    "blizzard": {
        "wind_speed": 1.20,
        "wind_direction_norm": 0.5,
        "skybox_exposure": 0.3,
        "skybox_tint_rgb": [0.7, 0.7, 0.8],
    },
}


class AtmosphericsTool(Tool):
    """Build an atmospherics dict for inclusion in the next DecisionPayload."""

    name = "atmospherics"
    description = (
        "Set the visible environment (sun position, color, wind, skybox) "
        "to match the current narrative. Call this when the story says "
        "the time of day or weather changes."
    )

    def call(
        self,
        time_of_day: str | None = None,
        weather: str | None = None,
        wind_direction_norm: float | None = None,
        transition_seconds: float = 2.0,
        **overrides: Any,
    ) -> dict[str, Any]:
        """
        Args:
            time_of_day: one of dawn/morning/noon/afternoon/dusk/night, or None
            weather: one of calm/breezy/stormy/blizzard, or None
            wind_direction_norm: override wind direction (0=N, 0.25=E, 0.5=S, 0.75=W)
            transition_seconds: how long to fade (0-60s, default 2)
            **overrides: any direct field override (sun_pitch_deg, etc.)

        Returns:
            dict matching `.shared/schemas/decision.schema.json` atmospherics shape.
            The orchestrator places it in DecisionPayload.atmospherics.
        """
        out: dict[str, Any] = {}

        if time_of_day:
            tod = time_of_day.lower()
            if tod not in PRESETS_TOD:
                raise ValueError(
                    f"unknown time_of_day {time_of_day!r} (want one of {list(PRESETS_TOD)})"
                )
            out.update(PRESETS_TOD[tod])

        if weather:
            wx = weather.lower()
            if wx not in PRESETS_WEATHER:
                raise ValueError(
                    f"unknown weather {weather!r} (want one of {list(PRESETS_WEATHER)})"
                )
            # weather overlays on top of TOD
            out.update(PRESETS_WEATHER[wx])

        if wind_direction_norm is not None:
            if not 0.0 <= wind_direction_norm <= 1.0:
                raise ValueError(f"wind_direction_norm {wind_direction_norm} out of [0..1] range")
            out["wind_direction_norm"] = wind_direction_norm

        # Direct overrides win over presets
        for k, v in overrides.items():
            out[k] = v

        if transition_seconds is not None:
            if not 0.0 <= transition_seconds <= 60.0:
                raise ValueError(f"transition_seconds {transition_seconds} out of [0..60] range")
            out["transition_seconds"] = float(transition_seconds)

        return out
