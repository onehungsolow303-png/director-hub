# tests/test_memory_tool.py
from director_hub.memory.manager import MemoryManager
from director_hub.toolbelt.memory_tool import MemoryTool


def test_memory_tool_searches_all_tiers():
    mgr = MemoryManager(persist=False)
    mgr.semantic.set("player_style", "prefers ranged combat")
    mgr.long.index({"text": "Goblin encounters work best at CR 1"})
    mgr.episodic.record({"session_id": "s1", "type": "combat_end", "outcome": "player_won"})

    tool = MemoryTool(mgr)
    result = tool.call(query="goblin combat", tier="all", k=5)

    assert result["ok"] is True
    assert len(result["results"]) >= 1


def test_memory_tool_semantic_only():
    mgr = MemoryManager(persist=False)
    mgr.semantic.set("forest_rule", "cap at 2 enemies")
    mgr.long.index({"text": "Something about dungeons"})

    tool = MemoryTool(mgr)
    result = tool.call(query="forest", tier="semantic", k=5)

    assert result["ok"] is True
    assert all(r["source"] == "semantic" for r in result["results"])


def test_memory_tool_empty_returns_ok():
    mgr = MemoryManager(persist=False)
    tool = MemoryTool(mgr)
    result = tool.call(query="anything", tier="all", k=5)

    assert result["ok"] is True
    assert result["results"] == []
