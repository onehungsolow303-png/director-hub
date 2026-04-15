# tests/test_encounter_selector.py
import tempfile
from pathlib import Path

from director_hub.content.encounter_selector import EncounterSelector
from director_hub.content.template_store import EncounterTemplate, TemplateStore
from director_hub.memory.manager import MemoryManager


def _make_store(tmp: str) -> tuple[TemplateStore, MemoryManager]:
    mgr = MemoryManager(persist=False)
    store = TemplateStore(template_dir=Path(tmp), memory=mgr)
    return store, mgr


def _forest_template(tid: str = "forest_01", **overrides) -> EncounterTemplate:
    defaults = dict(
        template_id=tid,
        name="Forest Ambush",
        min_xp=100,
        max_xp=300,
        party_size_range=[1, 4],
        biomes=["forest"],
        slots=[{"name": "Wolf", "behavior": "chase", "xp": 50}],
        party_counters=["all_melee"],
        party_rewards=["has_ranged"],
        tags=["beast", "forest"],
        design_intent="Basic forest threat",
        difficulty_context="Level 1-3",
        confidence=0.7,
        times_used=0,
    )
    defaults.update(overrides)
    return EncounterTemplate(**defaults)


def test_selector_picks_matching_biome():
    with tempfile.TemporaryDirectory() as tmp:
        store, mgr = _make_store(tmp)
        store.save(_forest_template("forest_01"))
        store.save(_forest_template("swamp_01", biomes=["swamp"], tags=["undead"]))

        selector = EncounterSelector(store, mgr)
        result = selector.select(
            biome="forest",
            party=[{"player_id": "p1", "class": "fighter", "level": 2}],
            xp_budget=200,
            scene_context={},
        )
        assert result is not None
        assert result.template_id == "forest_01"


def test_selector_returns_none_when_no_match():
    with tempfile.TemporaryDirectory() as tmp:
        store, mgr = _make_store(tmp)
        store.save(_forest_template("forest_01"))

        selector = EncounterSelector(store, mgr)
        result = selector.select(
            biome="desert",
            party=[{"player_id": "p1", "class": "fighter", "level": 2}],
            xp_budget=200,
            scene_context={},
        )
        assert result is None


def test_selector_prefers_narrative_match():
    with tempfile.TemporaryDirectory() as tmp:
        store, mgr = _make_store(tmp)
        store.save(_forest_template("generic_01", tags=["beast"]))
        store.save(
            _forest_template(
                "quest_01", tags=["undead", "ruins"], narrative_hook="The dead walk near the ruins"
            )
        )

        selector = EncounterSelector(store, mgr)
        result = selector.select(
            biome="forest",
            party=[{"player_id": "p1", "class": "fighter", "level": 2}],
            xp_budget=200,
            scene_context={"traveling_to": "Ashwick Ruins", "active_quest": "Clear the Ruins"},
        )
        assert result is not None
        assert result.template_id == "quest_01"


def test_selector_penalizes_recently_used():
    with tempfile.TemporaryDirectory() as tmp:
        store, mgr = _make_store(tmp)
        fresh = _forest_template("fresh_01", times_used=0)
        stale = _forest_template("stale_01", times_used=5)
        store.save(fresh)
        store.save(stale)

        selector = EncounterSelector(store, mgr)
        result = selector.select(
            biome="forest",
            party=[{"player_id": "p1", "class": "fighter", "level": 2}],
            xp_budget=200,
            scene_context={},
        )
        assert result is not None
        assert result.template_id == "fresh_01"
