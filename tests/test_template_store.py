# tests/test_template_store.py
import tempfile
from pathlib import Path

from director_hub.content.template_store import EncounterTemplate, TemplateStore
from director_hub.memory.manager import MemoryManager


def _sample_template(
    template_id: str = "test_ambush_01", biome: str = "forest"
) -> EncounterTemplate:
    return EncounterTemplate(
        template_id=template_id,
        name="Test Ambush",
        min_xp=100,
        max_xp=300,
        party_size_range=[1, 4],
        biomes=[biome],
        slots=[
            {"name": "Bandit", "behavior": "chase", "xp": 50, "damage_type": "slashing"},
            {"name": "Bandit", "behavior": "chase", "xp": 50, "damage_type": "slashing"},
        ],
        scaling={
            "per_extra_player": {"add_slot": {"name": "Bandit", "behavior": "chase", "xp": 50}},
            "max_slots": 5,
        },
        party_counters=["all_melee"],
        party_rewards=["has_ranged"],
        narrative_hook="Rough-looking figures step from the treeline",
        design_intent="Basic melee challenge",
        difficulty_context="Level 1-3",
        tags=["bandit", "melee", "ambush"],
    )


def test_store_save_and_load():
    with tempfile.TemporaryDirectory() as tmp:
        mgr = MemoryManager(persist=False)
        store = TemplateStore(template_dir=Path(tmp), memory=mgr)

        tpl = _sample_template()
        store.save(tpl)

        loaded = store.get("test_ambush_01")
        assert loaded is not None
        assert loaded.name == "Test Ambush"
        assert len(loaded.slots) == 2


def test_store_list_by_biome():
    with tempfile.TemporaryDirectory() as tmp:
        mgr = MemoryManager(persist=False)
        store = TemplateStore(template_dir=Path(tmp), memory=mgr)

        store.save(_sample_template("forest_01", "forest"))
        store.save(_sample_template("swamp_01", "swamp"))
        store.save(_sample_template("forest_02", "forest"))

        forest = store.list_by_biome("forest")
        assert len(forest) == 2

        swamp = store.list_by_biome("swamp")
        assert len(swamp) == 1


def test_store_prune_low_confidence():
    with tempfile.TemporaryDirectory() as tmp:
        mgr = MemoryManager(persist=False)
        store = TemplateStore(template_dir=Path(tmp), memory=mgr)

        tpl = _sample_template()
        tpl.confidence = 0.2
        tpl.times_used = 5
        tpl.generated_by = "director_hub"
        store.save(tpl)

        pruned = store.prune(confidence_threshold=0.3, min_uses=3)
        assert len(pruned) == 1
        assert store.get("test_ambush_01") is None


def test_store_never_prunes_hardcoded():
    with tempfile.TemporaryDirectory() as tmp:
        mgr = MemoryManager(persist=False)
        store = TemplateStore(template_dir=Path(tmp), memory=mgr)

        tpl = _sample_template()
        tpl.confidence = 0.1
        tpl.times_used = 10
        tpl.generated_by = "hard_coded"
        store.save(tpl)

        pruned = store.prune(confidence_threshold=0.3, min_uses=3)
        assert len(pruned) == 0
        assert store.get("test_ambush_01") is not None


def test_store_update_usage_stats():
    with tempfile.TemporaryDirectory() as tmp:
        mgr = MemoryManager(persist=False)
        store = TemplateStore(template_dir=Path(tmp), memory=mgr)

        store.save(_sample_template())
        store.record_usage("test_ambush_01", outcome_quality=0.8)

        tpl = store.get("test_ambush_01")
        assert tpl.times_used == 1
        assert tpl.average_outcome == 0.8


def test_store_memory_index_searchable():
    with tempfile.TemporaryDirectory() as tmp:
        mgr = MemoryManager(persist=False)
        store = TemplateStore(template_dir=Path(tmp), memory=mgr)

        store.save(_sample_template())

        results = mgr.long.search("bandit melee ambush", k=5)
        assert len(results) >= 1
