# tests/test_reflector.py
from director_hub.memory.manager import MemoryManager
from director_hub.reasoning.outcome import ComparisonResult, Surprise
from director_hub.reasoning.reflector import InlineReflector


def test_reflector_stores_lesson_on_surprise():
    mgr = MemoryManager(persist=False)
    reflector = InlineReflector(mgr)

    comparison = ComparisonResult(
        decision_id="d1",
        surprises=[
            Surprise(
                type="difficulty_mismatch",
                expected="medium",
                actual="deadly",
                significance="high",
            )
        ],
        should_store=True,
    )

    reflector.reflect(
        comparison=comparison,
        decision_summary="Sent 3 goblins at level 1 player in forest",
        use_llm=False,
    )

    results = mgr.long.search("difficulty", k=5)
    assert len(results) >= 1


def test_reflector_skips_routine_outcome():
    mgr = MemoryManager(persist=False)
    reflector = InlineReflector(mgr)

    comparison = ComparisonResult(
        decision_id="d1",
        surprises=[],
        player_signals=[],
        should_store=False,
    )

    reflector.reflect(
        comparison=comparison,
        decision_summary="Routine forest encounter",
        use_llm=False,
    )

    assert mgr.long.count() == 0
