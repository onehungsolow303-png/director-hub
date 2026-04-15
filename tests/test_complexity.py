# tests/test_complexity.py
from director_hub.reasoning.complexity import assess_complexity


def test_low_complexity_random_encounter():
    req = {
        "scene_context": {"biome": "forest", "location": "clearing", "location_safe": False},
        "actor_stats": {"hp": 20, "max_hp": 20},
    }
    result = assess_complexity(req)
    assert result.level == "low"
    assert result.token_budget == 500


def test_high_complexity_boss_encounter():
    req = {
        "scene_context": {
            "biome": "castle",
            "location": "throne_room",
            "npc_persona": "The Rot King",
            "location_safe": False,
        },
        "actor_stats": {"hp": 5, "max_hp": 30},
        "target_stats": {"name": "The Rot King"},
    }
    result = assess_complexity(req)
    assert result.level == "high"
    assert result.token_budget == 3000


def test_medium_complexity_named_npc():
    req = {
        "scene_context": {
            "biome": "forest",
            "location": "blacksmith",
            "npc_persona": "Gruk the Smith",
            "location_safe": True,
        },
        "actor_stats": {"hp": 15, "max_hp": 20},
    }
    result = assess_complexity(req)
    assert result.level == "medium"
    assert result.token_budget == 1500
