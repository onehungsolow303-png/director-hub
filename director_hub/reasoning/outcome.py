"""Compare predictions against actual outcomes. Detect surprises and player signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from director_hub.reasoning.prediction import Prediction


@dataclass
class OutcomeData:
    actual_difficulty: str = "unknown"
    actual_reaction: str = "unknown"
    actual_outcome: str = "unknown"
    player_hp_pct_after: float = 1.0
    content_skipped: bool = False
    session_ended: bool = False
    time_spent_seconds: float = 0.0
    party_outcomes: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class Surprise:
    type: str
    expected: str
    actual: str
    significance: str = "medium"


@dataclass
class ComparisonResult:
    decision_id: str
    surprises: list[Surprise] = field(default_factory=list)
    player_signals: list[Surprise] = field(default_factory=list)
    should_store: bool = False


def compare_outcome(prediction: Prediction, outcome: OutcomeData) -> ComparisonResult:
    surprises: list[Surprise] = []
    signals: list[Surprise] = []

    if prediction.expected_difficulty != outcome.actual_difficulty:
        surprises.append(
            Surprise(
                type="difficulty_mismatch",
                expected=prediction.expected_difficulty,
                actual=outcome.actual_difficulty,
                significance="high",
            )
        )

    if prediction.expected_player_reaction != outcome.actual_reaction:
        surprises.append(
            Surprise(
                type="player_reaction",
                expected=prediction.expected_player_reaction,
                actual=outcome.actual_reaction,
                significance="high",
            )
        )

    if prediction.expected_outcome != outcome.actual_outcome:
        surprises.append(
            Surprise(
                type="outcome_mismatch",
                expected=prediction.expected_outcome,
                actual=outcome.actual_outcome,
                significance="medium",
            )
        )

    if outcome.content_skipped:
        signals.append(
            Surprise(
                type="content_skipped",
                expected="engagement",
                actual="skipped",
                significance="medium",
            )
        )

    if outcome.session_ended:
        signals.append(
            Surprise(
                type="session_ended_after",
                expected="continued_play",
                actual="quit",
                significance="high",
            )
        )

    if outcome.player_hp_pct_after < 0.1 and prediction.expected_difficulty in ("easy", "medium"):
        signals.append(
            Surprise(
                type="near_death_unexpected",
                expected=prediction.expected_difficulty,
                actual=f"hp_at_{outcome.player_hp_pct_after:.0%}",
                significance="high",
            )
        )

    should_store = len(surprises) > 0 or len(signals) > 0

    return ComparisonResult(
        decision_id=prediction.decision_id,
        surprises=surprises,
        player_signals=signals,
        should_store=should_store,
    )
