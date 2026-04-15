# tests/test_outcome.py
from director_hub.reasoning.outcome import OutcomeData, compare_outcome
from director_hub.reasoning.prediction import Prediction


def test_surprise_detected_on_difficulty_mismatch():
    pred = Prediction(
        decision_id="d1",
        session_id="s1",
        expected_difficulty="medium",
        expected_player_reaction="engage_combat",
        expected_outcome="player_wins_with_damage",
        confidence=0.7,
    )
    outcome = OutcomeData(
        actual_difficulty="deadly",
        actual_reaction="engage_combat",
        actual_outcome="player_lost",
        player_hp_pct_after=0.0,
    )
    result = compare_outcome(pred, outcome)
    assert result.should_store is True
    assert any(s.type == "difficulty_mismatch" for s in result.surprises)


def test_no_surprise_when_prediction_matches():
    pred = Prediction(
        decision_id="d1",
        session_id="s1",
        expected_difficulty="easy",
        expected_player_reaction="engage_combat",
        expected_outcome="player_wins_easily",
        confidence=0.9,
    )
    outcome = OutcomeData(
        actual_difficulty="easy",
        actual_reaction="engage_combat",
        actual_outcome="player_wins_easily",
        player_hp_pct_after=0.9,
    )
    result = compare_outcome(pred, outcome)
    assert result.should_store is False
    assert len(result.surprises) == 0


def test_player_signal_detected_on_content_skip():
    pred = Prediction(
        decision_id="d1",
        session_id="s1",
        expected_player_reaction="explore",
        expected_outcome="player_explores",
    )
    outcome = OutcomeData(
        actual_reaction="ignore",
        actual_outcome="player_walked_past",
        player_hp_pct_after=0.8,
        content_skipped=True,
    )
    result = compare_outcome(pred, outcome)
    assert result.should_store is True
    assert any(s.type == "content_skipped" for s in result.player_signals)
