# tests/test_prediction.py
import tempfile
from pathlib import Path

from director_hub.reasoning.prediction import Prediction, PredictionRecorder


def test_record_and_retrieve():
    with tempfile.TemporaryDirectory() as tmp:
        recorder = PredictionRecorder(root=Path(tmp))
        pred = Prediction(
            decision_id="d1",
            session_id="s1",
            decision_type="encounter",
            expected_difficulty="medium",
            expected_player_reaction="engage_combat",
            expected_outcome="player_wins_with_damage",
            confidence=0.7,
            context_snapshot={"player_level": 2, "biome": "forest"},
        )
        recorder.record(pred)
        retrieved = recorder.get_latest("s1")
        assert retrieved is not None
        assert retrieved.decision_id == "d1"
        assert retrieved.expected_difficulty == "medium"


def test_extract_prediction_from_response():
    response = {
        "narrative_text": "You attack the goblin.",
        "stat_effects": [],
        "_prediction": {
            "expected_difficulty": "easy",
            "expected_player_reaction": "engage_combat",
            "expected_outcome": "player_wins_easily",
            "confidence": 0.9,
        },
    }
    pred = PredictionRecorder.extract_from_response(response, session_id="s1", decision_id="d1")
    assert pred is not None
    assert pred.expected_difficulty == "easy"
    assert pred.confidence == 0.9


def test_extract_returns_none_when_missing():
    response = {"narrative_text": "You rest.", "stat_effects": []}
    pred = PredictionRecorder.extract_from_response(response, session_id="s1", decision_id="d1")
    assert pred is None


def test_strip_prediction_from_response():
    response = {
        "narrative_text": "test",
        "_prediction": {"expected_difficulty": "easy"},
    }
    cleaned = PredictionRecorder.strip_from_response(response)
    assert "_prediction" not in cleaned
    assert cleaned["narrative_text"] == "test"
