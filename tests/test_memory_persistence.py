"""Persistence tests for episodic + semantic memory + the MemoryManager facade.

ShortTermMemory and LongTermMemory have their own dedicated test files;
this file covers the disk paths added in Round M.
"""
from __future__ import annotations

import json
from pathlib import Path

from director_hub.memory.episodic import EpisodicMemory
from director_hub.memory.manager import MemoryManager
from director_hub.memory.semantic import SemanticMemory


# ---------------------------------------------------------------- EpisodicMemory


def test_episodic_records_in_memory_and_to_disk(tmp_path: Path):
    mem = EpisodicMemory(root=tmp_path / "episodic", persist=True)
    mem.record({"session_id": "s1", "kind": "combat_start", "encounter": "goblin"})
    mem.record({"session_id": "s1", "kind": "kill", "target": "goblin"})
    mem.record({"session_id": "s2", "kind": "combat_start", "encounter": "wolf"})

    # In-memory
    assert len(mem.all()) == 3

    # On disk: per-session JSONL files
    s1_file = tmp_path / "episodic" / "s1.jsonl"
    s2_file = tmp_path / "episodic" / "s2.jsonl"
    assert s1_file.exists()
    assert s2_file.exists()
    s1_lines = s1_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(s1_lines) == 2
    parsed = [json.loads(l) for l in s1_lines]
    assert parsed[0]["kind"] == "combat_start"
    assert parsed[1]["kind"] == "kill"


def test_episodic_for_session_filters(tmp_path: Path):
    mem = EpisodicMemory(root=tmp_path / "episodic", persist=True)
    mem.record({"session_id": "s1", "kind": "a"})
    mem.record({"session_id": "s2", "kind": "b"})
    mem.record({"session_id": "s1", "kind": "c"})

    s1 = mem.for_session("s1")
    assert len(s1) == 2
    assert {e["kind"] for e in s1} == {"a", "c"}

    s2 = mem.for_session("s2")
    assert len(s2) == 1
    assert s2[0]["kind"] == "b"


def test_episodic_for_session_includes_disk_history(tmp_path: Path):
    """A new EpisodicMemory instance (e.g., after Director Hub restart)
    should still see events its predecessor wrote to disk."""
    root = tmp_path / "episodic"
    first = EpisodicMemory(root=root, persist=True)
    first.record({"session_id": "s1", "kind": "before_restart"})

    # Simulate a restart
    second = EpisodicMemory(root=root, persist=True)
    found = second.for_session("s1")
    assert len(found) == 1
    assert found[0]["kind"] == "before_restart"


def test_episodic_clear_keeps_disk(tmp_path: Path):
    mem = EpisodicMemory(root=tmp_path / "episodic", persist=True)
    mem.record({"session_id": "s1", "kind": "a"})
    mem.clear()
    assert mem.all() == []
    # Disk file still there
    f = tmp_path / "episodic" / "s1.jsonl"
    assert f.exists()


def test_episodic_wipe_removes_disk(tmp_path: Path):
    mem = EpisodicMemory(root=tmp_path / "episodic", persist=True)
    mem.record({"session_id": "s1", "kind": "a"})
    mem.wipe()
    assert mem.all() == []
    f = tmp_path / "episodic" / "s1.jsonl"
    assert not f.exists()


def test_episodic_in_memory_only(tmp_path: Path):
    mem = EpisodicMemory(root=tmp_path / "episodic", persist=False)
    mem.record({"session_id": "s1", "kind": "a"})
    assert len(mem.all()) == 1
    # No disk file
    f = tmp_path / "episodic" / "s1.jsonl"
    assert not f.exists()


# ---------------------------------------------------------------- SemanticMemory


def test_semantic_set_and_get(tmp_path: Path):
    mem = SemanticMemory(path=tmp_path / "semantic.json", persist=True)
    mem.set("npc.innkeeper.disposition", "friendly")
    mem.set("faction.thieves.reputation", -3)
    assert mem.get("npc.innkeeper.disposition") == "friendly"
    assert mem.get("faction.thieves.reputation") == -3
    assert mem.get("npc.unknown", default="neutral") == "neutral"


def test_semantic_persists_across_instances(tmp_path: Path):
    path = tmp_path / "semantic.json"
    first = SemanticMemory(path=path, persist=True)
    first.set("world.day", 7)

    second = SemanticMemory(path=path, persist=True)
    assert second.get("world.day") == 7


def test_semantic_delete(tmp_path: Path):
    mem = SemanticMemory(path=tmp_path / "semantic.json", persist=True)
    mem.set("k", "v")
    assert mem.delete("k") is True
    assert mem.get("k") is None
    assert mem.delete("nonexistent") is False


def test_semantic_wipe(tmp_path: Path):
    mem = SemanticMemory(path=tmp_path / "semantic.json", persist=True)
    mem.set("k", "v")
    mem.wipe()
    assert mem.all() == {}
    assert not (tmp_path / "semantic.json").exists()


# ---------------------------------------------------------------- MemoryManager


def test_manager_constructs_all_four_tiers(tmp_path: Path):
    mgr = MemoryManager(persist=False, state_root=tmp_path)
    assert mgr.short is not None
    assert mgr.episodic is not None
    assert mgr.semantic is not None
    assert mgr.long is not None
    # Long-term should be the dict backend in non-persist mode
    assert mgr.long.backend_name == "dict"


def test_manager_round_trip_through_all_tiers(tmp_path: Path):
    mgr = MemoryManager(persist=False, state_root=tmp_path)
    mgr.short.add("thinking about goblins")
    mgr.episodic.record({"session_id": "s1", "kind": "combat"})
    mgr.semantic.set("npc.x", "hostile")
    mgr.long.index({"text": "the player slew a wolf"})

    assert mgr.short.recent() == ["thinking about goblins"]
    assert len(mgr.episodic.all()) == 1
    assert mgr.semantic.get("npc.x") == "hostile"
    assert mgr.long.count() == 1
