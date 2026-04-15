# tests/test_session_review.py
from director_hub.memory.manager import MemoryManager
from director_hub.reasoning.session_review import SessionReviewer


def test_session_review_deterministic():
    mgr = MemoryManager(persist=False)

    mgr.episodic.record(
        {"session_id": "s1", "type": "combat_start", "enemies": 3, "biome": "forest"}
    )
    mgr.episodic.record(
        {"session_id": "s1", "type": "combat_end", "outcome": "player_won", "hp_pct": 0.2}
    )
    mgr.episodic.record({"session_id": "s1", "type": "quest_offered", "quest": "shrine_quest"})
    mgr.episodic.record({"session_id": "s1", "type": "quest_skipped", "quest": "shrine_quest"})

    mgr.long.index(
        {
            "text": "Forest encounters with 3+ enemies are too hard for early players",
            "category": "lesson",
            "metadata": {"confirmed_count": 2},
        }
    )
    mgr.semantic.set("test_rule", "existing rule")

    reviewer = SessionReviewer(mgr)
    result = reviewer.review(session_id="s1", use_llm=False)

    assert "session_summary" in result
    assert isinstance(result["events_reviewed"], int)


def test_session_review_empty_session():
    mgr = MemoryManager(persist=False)
    reviewer = SessionReviewer(mgr)
    result = reviewer.review(session_id="empty_session", use_llm=False)

    assert result["events_reviewed"] == 0
