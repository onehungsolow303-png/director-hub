"""Score request complexity to determine memory injection budget."""

from __future__ import annotations

from dataclasses import dataclass

_BUDGETS = {"low": 500, "medium": 1500, "high": 3000}


@dataclass(frozen=True)
class ComplexityResult:
    level: str  # "low" | "medium" | "high"
    token_budget: int
    signals: list[str]


def assess_complexity(action_request: dict) -> ComplexityResult:
    """Score a request as low/medium/high complexity based on context signals."""
    score = 0
    signals: list[str] = []

    scene = action_request.get("scene_context") or {}
    actor = action_request.get("actor_stats") or {}
    target = action_request.get("target_stats") or {}

    if scene.get("npc_persona"):
        score += 2
        signals.append("npc_persona_present")

    target_name = target.get("name", "")
    if target_name and any(
        w in target_name.lower() for w in ("king", "lord", "boss", "dragon", "lich")
    ):
        score += 3
        signals.append("boss_target")

    location = scene.get("location", "")
    if any(w in location.lower() for w in ("throne", "boss", "final", "castle")):
        score += 2
        signals.append("major_location")

    hp = actor.get("hp", 1)
    max_hp = actor.get("max_hp", 1)
    if max_hp > 0 and hp / max_hp < 0.25:
        score += 1
        signals.append("player_critical_hp")

    if not scene.get("location_safe", True):
        score += 1
        signals.append("unsafe_location")

    party = action_request.get("party") or []
    if len(party) > 1:
        score += 1
        signals.append("party_present")
    if len(party) >= 4:
        score += 1
        signals.append("large_party")

    if score >= 4:
        level = "high"
    elif score >= 2:
        level = "medium"
    else:
        level = "low"

    return ComplexityResult(level=level, token_budget=_BUDGETS[level], signals=signals)
