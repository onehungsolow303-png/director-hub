"""Tests for the durable game event store (SQLite WAL)."""

import json
from pathlib import Path

import pytest

from director_hub.persistence.game_store import GameStore


@pytest.fixture()
def store(tmp_path: Path) -> GameStore:
    db = tmp_path / "test_events.db"
    s = GameStore(db_path=db)
    yield s
    s.close()


class TestSessionLifecycle:
    def test_start_and_get_session(self, store: GameStore):
        sid = store.start_session(player_id="p1")
        session = store.get_session(sid)
        assert session is not None
        assert session["player_id"] == "p1"
        assert session["status"] == "active"
        assert session["ended_at"] is None

    def test_end_session(self, store: GameStore):
        sid = store.start_session(player_id="p1")
        store.end_session(sid)
        session = store.get_session(sid)
        assert session["status"] == "completed"
        assert session["ended_at"] is not None

    def test_save_snapshot_persisted(self, store: GameStore):
        snapshot = {"HP": 20, "Level": 3, "Gold": 150}
        sid = store.start_session(player_id="p1", save_snapshot=snapshot)
        session = store.get_session(sid)
        loaded = json.loads(session["save_snapshot_json"])
        assert loaded["HP"] == 20
        assert loaded["Level"] == 3

    def test_recent_sessions_ordered(self, store: GameStore):
        s1 = store.start_session(player_id="p1")
        store.end_session(s1)
        s2 = store.start_session(player_id="p1")
        store.end_session(s2)
        s3 = store.start_session(player_id="p1")

        recent = store.get_recent_sessions("p1", limit=2)
        assert len(recent) == 2
        assert recent[0]["id"] == s3  # most recent first
        assert recent[1]["id"] == s2

    def test_sessions_filtered_by_player(self, store: GameStore):
        store.start_session(player_id="p1")
        store.start_session(player_id="p2")
        assert len(store.get_recent_sessions("p1")) == 1
        assert len(store.get_recent_sessions("p2")) == 1


class TestCrashRecovery:
    def test_detect_crashed_sessions(self, store: GameStore):
        sid = store.start_session(player_id="p1")
        # Never ended — simulates a crash
        crashed = store.detect_crashed_sessions()
        assert len(crashed) == 1
        assert crashed[0]["id"] == sid

    def test_no_false_positives(self, store: GameStore):
        sid = store.start_session(player_id="p1")
        store.end_session(sid)
        assert store.detect_crashed_sessions() == []

    def test_recover_crashed_session(self, store: GameStore):
        sid = store.start_session(player_id="p1")
        store.record_event(sid, "p1", "action", {"input": "attack goblin"})
        store.record_event(sid, "p1", "action", {"input": "cast heal"})

        info = store.recover_crashed_session(sid)
        assert info["session_id"] == sid
        assert info["event_count"] == 2
        assert info["last_event_type"] == "action"
        assert "crashed after 2 events" in info["recovery_summary"]

        session = store.get_session(sid)
        assert session["status"] == "crashed"
        assert session["recovery_summary"] is not None

    def test_recover_empty_crashed_session(self, store: GameStore):
        sid = store.start_session(player_id="p1")
        info = store.recover_crashed_session(sid)
        assert info["event_count"] == 0
        assert info["last_event_type"] == "none"


class TestEvents:
    def test_record_and_retrieve_events(self, store: GameStore):
        sid = store.start_session(player_id="p1")
        e1 = store.record_event(sid, "p1", "action", {"input": "explore"})
        e2 = store.record_event(sid, "p1", "npc_interaction", {"npc": "garth"})

        assert e1 > 0
        assert e2 > e1

        events = store.get_session_events(sid)
        assert len(events) == 2

    def test_key_events_filter(self, store: GameStore):
        sid = store.start_session(player_id="p1")
        store.record_event(sid, "p1", "action", {"input": "walk"})
        store.record_event(sid, "p1", "npc_interaction", {"npc": "garth"})
        store.record_event(sid, "p1", "quest_update", {"quest": "clear mines"})
        store.record_event(sid, "p1", "action", {"input": "rest"})

        key = store.get_key_events(sid)
        assert len(key) == 2  # npc_interaction + quest_update, not actions

    def test_event_count(self, store: GameStore):
        sid = store.start_session(player_id="p1")
        assert store.session_event_count(sid) == 0
        store.record_event(sid, "p1", "action", {"input": "test"})
        assert store.session_event_count(sid) == 1


class TestDecisionLog:
    def test_record_and_retrieve_decisions(self, store: GameStore):
        sid = store.start_session(player_id="p1")
        eid = store.record_event(sid, "p1", "action", {"input": "attack"})
        did = store.record_decision(
            session_id=sid,
            event_id=eid,
            request={"player_input": "attack"},
            response={"narrative_text": "You strike the goblin!"},
            prediction={"expected_hp_change": -5},
        )
        assert did > 0

        decisions = store.get_session_decisions(sid)
        assert len(decisions) == 1
        assert json.loads(decisions[0]["request_json"])["player_input"] == "attack"

    def test_update_outcome_and_lessons(self, store: GameStore):
        sid = store.start_session(player_id="p1")
        eid = store.record_event(sid, "p1", "action", {"input": "heal"})
        did = store.record_decision(
            session_id=sid,
            event_id=eid,
            request={},
            response={},
        )
        store.update_decision_outcome(
            did,
            outcome={"hp_after": 20},
            surprise=True,
            lesson="Player heals when below 50% HP",
        )

        lessons = store.get_lessons(session_id=sid)
        assert len(lessons) == 1
        assert lessons[0]["lesson_text"] == "Player heals when below 50% HP"
        assert lessons[0]["surprise_detected"] == 1

    def test_get_all_lessons(self, store: GameStore):
        s1 = store.start_session(player_id="p1")
        d1 = store.record_decision(s1, None, {}, {})
        store.update_decision_outcome(d1, {}, surprise=True, lesson="Lesson 1")

        s2 = store.start_session(player_id="p1")
        d2 = store.record_decision(s2, None, {}, {})
        store.update_decision_outcome(d2, {}, surprise=True, lesson="Lesson 2")

        all_lessons = store.get_lessons(limit=10)
        assert len(all_lessons) == 2


class TestStats:
    def test_totals(self, store: GameStore):
        assert store.total_sessions() == 0
        assert store.total_events() == 0

        sid = store.start_session(player_id="p1")
        store.record_event(sid, "p1", "action", {})
        store.record_event(sid, "p1", "action", {})

        assert store.total_sessions() == 1
        assert store.total_events() == 2


class TestWALMode:
    def test_wal_mode_enabled(self, store: GameStore):
        mode = store._con.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"

    def test_foreign_keys_enabled(self, store: GameStore):
        fk = store._con.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1
