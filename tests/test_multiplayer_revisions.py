from director_hub.memory.manager import MemoryManager
from director_hub.memory.retriever import MemoryRetriever
from director_hub.reasoning.complexity import assess_complexity
from director_hub.reasoning.outcome import OutcomeData, compare_outcome
from director_hub.reasoning.prediction import Prediction


def test_prediction_supports_per_player_outcomes():
    pred = Prediction(
        decision_id="d1",
        session_id="s1",
        expected_outcomes_by_player={
            "p1": {"expected_difficulty": "medium", "expected_outcome": "takes_moderate_damage"},
            "p2": {"expected_difficulty": "easy", "expected_outcome": "uses_spell_slots"},
        },
    )
    assert "p1" in pred.expected_outcomes_by_player
    assert pred.expected_outcomes_by_player["p2"]["expected_outcome"] == "uses_spell_slots"


def test_prediction_backwards_compatible():
    pred = Prediction(decision_id="d1", session_id="s1", expected_difficulty="medium")
    assert pred.expected_outcomes_by_player == {}
    assert pred.expected_difficulty == "medium"


def test_outcome_data_supports_party():
    outcome = OutcomeData(
        party_outcomes={"p1": {"hp_pct_after": 0.3}, "p2": {"hp_pct_after": 0.8}},
    )
    assert outcome.party_outcomes["p1"]["hp_pct_after"] == 0.3


def test_outcome_backwards_compatible():
    outcome = OutcomeData(player_hp_pct_after=0.5)
    assert outcome.player_hp_pct_after == 0.5
    assert outcome.party_outcomes == {}


def test_complexity_considers_party():
    req = {
        "scene_context": {"biome": "forest", "location_safe": False},
        "actor_stats": {"hp": 20, "max_hp": 20},
        "party": [
            {"player_id": "p1", "class": "fighter", "level": 3},
            {"player_id": "p2", "class": "wizard", "level": 3},
        ],
    }
    result = assess_complexity(req)
    assert "party_present" in result.signals


def test_complexity_works_without_party():
    req = {
        "scene_context": {"biome": "forest", "location_safe": False},
        "actor_stats": {"hp": 20, "max_hp": 20},
    }
    result = assess_complexity(req)
    assert "party_present" not in result.signals


def test_retriever_accepts_player_id():
    mgr = MemoryManager(persist=False)
    mgr.semantic.set("player_p1_style", "prefers ranged combat")
    mgr.semantic.set("player_p2_style", "aggressive melee")
    mgr.semantic.set("global_rule", "some global rule")

    retriever = MemoryRetriever(mgr)
    block = retriever.assemble(
        action_request={"scene_context": {"biome": "forest"}, "actor_stats": {}},
        session_id="s1",
        token_budget=1500,
        player_id="p1",
    )
    assert "player_p1_style" in block
    assert "global_rule" in block
    # Should NOT contain p2's player-specific rules
    assert "player_p2_style" not in block
