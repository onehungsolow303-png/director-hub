"""Boot-time deep scan — assembles a full memory brief for a new game session.

Called once at game boot (POST /session/boot). Performs crash recovery, loads
prior session history, semantic facts, long-term lessons, and dev artifacts.

Design spec: .shared/docs/superpowers/specs/2026-04-16-durable-game-memory-design.md
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from director_hub.memory.manager import MemoryManager
from director_hub.persistence.game_store import GameStore
from director_hub.project_tracker.narrative_gen import render
from director_hub.project_tracker.scanner import full_scan

logger = logging.getLogger(__name__)


def deep_scan(
    game_store: GameStore,
    memory: MemoryManager,
    player_id: str,
    save_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform a full boot-time deep scan. Returns the boot response payload."""
    started = time.monotonic()

    # 1. Crash recovery
    crashed = _recover_crashed_sessions(game_store)

    # 2. Prior sessions
    prior_sessions = _load_prior_sessions(game_store, player_id)

    # 3. Semantic facts
    semantic_facts = memory.semantic.all()

    # 4. Long-term lessons (vector search for general context)
    long_term_lessons = _load_long_term_lessons(memory)

    # 5. Dev context (expanded scanner)
    dev_context = _load_dev_context()

    # 6. Player summary
    player_summary = _summarize_player(save_data) if save_data else None

    elapsed = int((time.monotonic() - started) * 1000)

    return {
        "ok": True,
        "scan_elapsed_ms": elapsed,
        "crashed_sessions": crashed,
        "memory_brief": {
            "dev_context": dev_context,
            "prior_sessions": prior_sessions,
            "semantic_facts": semantic_facts,
            "long_term_lessons": long_term_lessons,
            "player_summary": player_summary,
        },
    }


def _recover_crashed_sessions(store: GameStore) -> list[dict[str, Any]]:
    """Detect and recover any sessions left in 'active' state."""
    crashed_sessions = store.detect_crashed_sessions()
    recovered = []
    for session in crashed_sessions:
        session_id = session["id"]
        logger.warning("[DeepScan] Recovering crashed session %s", session_id)
        info = store.recover_crashed_session(session_id)
        recovered.append(info)
    if recovered:
        logger.info("[DeepScan] Recovered %d crashed session(s)", len(recovered))
    return recovered


def _load_prior_sessions(
    store: GameStore,
    player_id: str,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Load summaries of the last N sessions for this player."""
    sessions = store.get_recent_sessions(player_id, limit=limit)
    result = []
    for sess in sessions:
        session_id = sess["id"]
        events = store.get_session_events(session_id, limit=200)
        key_events = store.get_key_events(session_id)
        decisions = store.get_session_decisions(session_id, limit=10)
        lessons = store.get_lessons(session_id=session_id, limit=5)

        # Extract readable summaries from key events
        event_summaries = []
        for ev in key_events[:20]:
            try:
                payload = json.loads(ev.get("payload_json", "{}"))
                summary = payload.get("summary") or payload.get("description") or ev["event_type"]
                event_summaries.append(summary)
            except (json.JSONDecodeError, KeyError):
                event_summaries.append(ev.get("event_type", "unknown"))

        lesson_texts = [d.get("lesson_text", "") for d in lessons if d.get("lesson_text")]

        result.append(
            {
                "session_id": session_id,
                "started_at": sess.get("started_at"),
                "status": sess.get("status"),
                "event_count": len(events),
                "decision_count": len(decisions),
                "key_events": event_summaries[:10],
                "lessons_learned": lesson_texts[:5],
            }
        )

    return result


def _load_long_term_lessons(memory: MemoryManager, k: int = 10) -> list[dict[str, Any]]:
    """Pull the most relevant long-term lessons from vector store."""
    # Search with broad queries to get a diverse set
    queries = [
        "player combat behavior patterns",
        "NPC interaction outcomes",
        "quest and exploration decisions",
    ]
    seen_texts: set[str] = set()
    lessons: list[dict[str, Any]] = []
    for q in queries:
        for doc in memory.long.search(q, k=k):
            text = doc.get("text", "")
            if text and text not in seen_texts:
                seen_texts.add(text)
                lessons.append(doc)
    return lessons[:k]


def _load_dev_context() -> str:
    """Run the expanded project-state scanner and render narrative."""
    try:
        snapshot = full_scan()
        return render(snapshot)
    except Exception as e:
        logger.warning("[DeepScan] Dev context scan failed: %s", e)
        return f"(Dev context unavailable: {e})"


def _summarize_player(save_data: dict[str, Any]) -> str:
    """Generate a one-line player summary from save data."""
    parts = []
    level = save_data.get("Level")
    if level:
        parts.append(f"Level {level}")

    model_id = save_data.get("ModelId", "")
    if model_id:
        parts.append(model_id.replace("_", " "))

    hp = save_data.get("HP")
    max_hp = save_data.get("MaxHP")
    if hp is not None and max_hp:
        parts.append(f"{hp}/{max_hp} HP")

    gold = save_data.get("Gold")
    if gold is not None:
        parts.append(f"{gold} gold")

    explored = save_data.get("ExploredHexes")
    if explored:
        n = len(explored) if isinstance(explored, (list, set)) else 0
        if n:
            parts.append(f"{n} hexes explored")

    return ", ".join(parts) if parts else "New character"
