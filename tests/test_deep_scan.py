"""Tests for boot-time deep scan orchestrator."""

from pathlib import Path

import pytest

from director_hub.boot.deep_scan import deep_scan
from director_hub.memory.manager import MemoryManager
from director_hub.persistence.game_store import GameStore


@pytest.fixture()
def store(tmp_path: Path) -> GameStore:
    s = GameStore(db_path=tmp_path / "test.db")
    yield s
    s.close()


@pytest.fixture()
def memory(tmp_path: Path) -> MemoryManager:
    return MemoryManager(persist=False, state_root=tmp_path / "state")


class TestDeepScan:
    def test_empty_scan_returns_ok(self, store: GameStore, memory: MemoryManager):
        result = deep_scan(store, memory, player_id="p1")
        assert result["ok"] is True
        assert result["scan_elapsed_ms"] >= 0
        assert result["crashed_sessions"] == []
        assert "memory_brief" in result

    def test_memory_brief_structure(self, store: GameStore, memory: MemoryManager):
        result = deep_scan(store, memory, player_id="p1")
        brief = result["memory_brief"]
        assert "dev_context" in brief
        assert "prior_sessions" in brief
        assert "semantic_facts" in brief
        assert "long_term_lessons" in brief
        assert brief["player_summary"] is None  # no save data provided

    def test_with_save_data(self, store: GameStore, memory: MemoryManager):
        save = {"Level": 5, "ModelId": "Human_Fighter", "HP": 35, "MaxHP": 40, "Gold": 500}
        result = deep_scan(store, memory, player_id="p1", save_data=save)
        summary = result["memory_brief"]["player_summary"]
        assert "Level 5" in summary
        assert "Human Fighter" in summary
        assert "35/40 HP" in summary
        assert "500 gold" in summary

    def test_crash_recovery(self, store: GameStore, memory: MemoryManager):
        # Simulate a crashed session
        sid = store.start_session(player_id="p1")
        store.record_event(sid, "p1", "action", {"input": "attack dragon"})
        store.record_event(sid, "p1", "action", {"input": "cast fireball"})
        # Never ended — crash!

        result = deep_scan(store, memory, player_id="p1")
        assert len(result["crashed_sessions"]) == 1
        assert result["crashed_sessions"][0]["event_count"] == 2

        # Session should now be marked crashed
        session = store.get_session(sid)
        assert session["status"] == "crashed"

    def test_prior_sessions_loaded(self, store: GameStore, memory: MemoryManager):
        # Create and close a session
        sid = store.start_session(player_id="p1")
        store.record_event(sid, "p1", "npc_interaction", {"summary": "Talked to Garth"})
        store.end_session(sid)

        result = deep_scan(store, memory, player_id="p1")
        prior = result["memory_brief"]["prior_sessions"]
        assert len(prior) == 1
        assert prior[0]["status"] == "completed"
        assert prior[0]["event_count"] >= 1

    def test_semantic_facts_included(self, store: GameStore, memory: MemoryManager):
        memory.semantic.set("npc_garth_reputation", "friendly")
        memory.semantic.set("quest_active", "clear_mines")

        result = deep_scan(store, memory, player_id="p1")
        facts = result["memory_brief"]["semantic_facts"]
        assert facts["npc_garth_reputation"] == "friendly"
        assert facts["quest_active"] == "clear_mines"

    def test_dev_context_is_string(self, store: GameStore, memory: MemoryManager):
        result = deep_scan(store, memory, player_id="p1")
        assert isinstance(result["memory_brief"]["dev_context"], str)
        assert len(result["memory_brief"]["dev_context"]) > 0
