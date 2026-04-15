# tests/test_encounter_designer.py
import tempfile
from pathlib import Path

from director_hub.content.encounter_designer import EncounterDesigner
from director_hub.content.template_store import TemplateStore
from director_hub.memory.manager import MemoryManager


def test_designer_generates_deterministic():
    with tempfile.TemporaryDirectory() as tmp:
        mgr = MemoryManager(persist=False)
        store = TemplateStore(template_dir=Path(tmp), memory=mgr)

        designer = EncounterDesigner(store, mgr)
        templates = designer.design(
            gaps={"missing_biomes": ["swamp"]},
            player_context={"level": 3, "classes": ["fighter", "wizard"]},
            lessons=["Forest encounters with 3+ enemies were too hard"],
            use_llm=False,
        )

        assert len(templates) >= 1
        assert templates[0].biomes == ["swamp"]
        assert store.get(templates[0].template_id) is not None


def test_designer_respects_max_templates():
    with tempfile.TemporaryDirectory() as tmp:
        mgr = MemoryManager(persist=False)
        store = TemplateStore(template_dir=Path(tmp), memory=mgr)

        # Fill store to max
        for i in range(100):
            from director_hub.content.template_store import EncounterTemplate

            store.save(
                EncounterTemplate(
                    template_id=f"fill_{i}",
                    name=f"Fill {i}",
                    biomes=["forest"],
                    slots=[{"name": "Wolf", "behavior": "chase", "xp": 50}],
                )
            )

        designer = EncounterDesigner(store, mgr, max_templates=100)
        designer.design(
            gaps={"missing_biomes": ["swamp"]},
            player_context={"level": 3},
            lessons=[],
            use_llm=False,
        )

        # Should prune before adding
        assert store.count() <= 100
