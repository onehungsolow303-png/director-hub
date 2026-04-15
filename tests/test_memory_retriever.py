# tests/test_memory_retriever.py
from director_hub.memory.manager import MemoryManager
from director_hub.memory.retriever import MemoryRetriever


def test_retriever_assembles_context_block():
    mgr = MemoryManager(persist=False)
    mgr.semantic.set("goblin_verdict", "too hard for level 1")
    mgr.long.index({"text": "Forest encounters should cap at 2 enemies", "category": "encounter"})
    mgr.episodic.record({"session_id": "s1", "type": "combat_start", "enemies": 2})

    retriever = MemoryRetriever(mgr)
    block = retriever.assemble(
        action_request={"scene_context": {"biome": "forest"}, "actor_stats": {}},
        session_id="s1",
        token_budget=1500,
    )

    assert "## Director Memory" in block
    assert "goblin_verdict" in block
    assert "Forest encounters" in block
    assert "combat_start" in block


def test_retriever_respects_budget_low():
    mgr = MemoryManager(persist=False)
    for i in range(20):
        mgr.long.index({"text": f"Lesson number {i} about encounters", "category": "encounter"})

    retriever = MemoryRetriever(mgr)
    block = retriever.assemble(
        action_request={"scene_context": {}, "actor_stats": {}},
        session_id="s1",
        token_budget=500,
    )

    assert block.count("Lesson number") <= 5


def test_retriever_empty_memory_returns_minimal_block():
    mgr = MemoryManager(persist=False)
    retriever = MemoryRetriever(mgr)
    block = retriever.assemble(
        action_request={"scene_context": {}, "actor_stats": {}},
        session_id="s1",
        token_budget=500,
    )

    assert "## Director Memory" in block
