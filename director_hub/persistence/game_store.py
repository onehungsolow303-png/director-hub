"""SQLite WAL-backed game event store.

Provides durable persistence for game sessions, player actions, LLM decisions,
and crash recovery. WAL mode ensures that incomplete writes from crashes are
rolled back automatically — only committed transactions survive.

Design spec: .shared/docs/superpowers/specs/2026-04-16-durable-game-memory-design.md
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path("C:/Dev/.shared/state/game_events.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS game_sessions (
    id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    save_snapshot_json TEXT,
    recovery_summary TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES game_sessions(id),
    player_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_player ON events(player_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);

CREATE TABLE IF NOT EXISTS decision_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES game_sessions(id),
    event_id INTEGER REFERENCES events(id),
    request_json TEXT NOT NULL,
    response_json TEXT NOT NULL,
    prediction_json TEXT,
    outcome_json TEXT,
    surprise_detected INTEGER DEFAULT 0,
    lesson_text TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_decision_session ON decision_log(session_id);
"""


class GameStore:
    """Durable game event store backed by SQLite with WAL journaling."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(str(self._db_path), timeout=10, check_same_thread=False)
        self._con.row_factory = sqlite3.Row
        self._con.execute("PRAGMA journal_mode = WAL")
        self._con.execute("PRAGMA synchronous = NORMAL")
        self._con.execute("PRAGMA foreign_keys = ON")
        self._con.executescript(_SCHEMA)
        self._con.commit()

    def close(self) -> None:
        self._con.close()

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def start_session(
        self,
        player_id: str,
        save_snapshot: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> str:
        """Create a new active game session. Returns session_id."""
        session_id = session_id or str(uuid.uuid4())
        now = _now()
        self._con.execute(
            "INSERT INTO game_sessions (id, player_id, started_at, status, save_snapshot_json) "
            "VALUES (?, ?, ?, 'active', ?)",
            (session_id, player_id, now, json.dumps(save_snapshot) if save_snapshot else None),
        )
        self._con.commit()
        return session_id

    def end_session(self, session_id: str) -> None:
        """Mark a session as completed."""
        self._con.execute(
            "UPDATE game_sessions SET status = 'completed', ended_at = ? WHERE id = ?",
            (_now(), session_id),
        )
        self._con.commit()

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        cur = self._con.execute("SELECT * FROM game_sessions WHERE id = ?", (session_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_recent_sessions(
        self,
        player_id: str,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Most recent sessions for a player, newest first."""
        cur = self._con.execute(
            "SELECT * FROM game_sessions WHERE player_id = ? ORDER BY started_at DESC LIMIT ?",
            (player_id, limit),
        )
        return [dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Crash detection & recovery
    # ------------------------------------------------------------------

    def detect_crashed_sessions(self) -> list[dict[str, Any]]:
        """Find sessions that are still 'active' (never properly ended)."""
        cur = self._con.execute(
            "SELECT * FROM game_sessions WHERE status = 'active' ORDER BY started_at DESC"
        )
        return [dict(r) for r in cur.fetchall()]

    def recover_crashed_session(self, session_id: str) -> dict[str, Any]:
        """Mark a crashed session and generate a recovery summary."""
        event_count = self._con.execute(
            "SELECT COUNT(*) FROM events WHERE session_id = ?", (session_id,)
        ).fetchone()[0]

        last_event = self._con.execute(
            "SELECT * FROM events WHERE session_id = ? ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchone()

        last_type = dict(last_event)["event_type"] if last_event else "none"
        last_time = dict(last_event)["created_at"] if last_event else "unknown"

        summary = (
            f"Session crashed after {event_count} events. Last event: {last_type} at {last_time}"
        )

        self._con.execute(
            "UPDATE game_sessions SET status = 'crashed', ended_at = ?, recovery_summary = ? "
            "WHERE id = ?",
            (_now(), summary, session_id),
        )
        self._con.commit()

        return {
            "session_id": session_id,
            "event_count": event_count,
            "last_event_type": last_type,
            "recovery_summary": summary,
        }

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _ensure_session(self, session_id: str, player_id: str) -> None:
        """Auto-create a session row if it doesn't exist (graceful for tests/fallback)."""
        existing = self._con.execute(
            "SELECT 1 FROM game_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not existing:
            self._con.execute(
                "INSERT INTO game_sessions (id, player_id, started_at, status) "
                "VALUES (?, ?, ?, 'active')",
                (session_id, player_id, _now()),
            )

    def record_event(
        self,
        session_id: str,
        player_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> int:
        """Record a game event. Returns event_id."""
        self._ensure_session(session_id, player_id)
        cur = self._con.execute(
            "INSERT INTO events (session_id, player_id, event_type, payload_json) "
            "VALUES (?, ?, ?, ?)",
            (session_id, player_id, event_type, json.dumps(payload, default=str)),
        )
        self._con.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_session_events(
        self,
        session_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        cur = self._con.execute(
            "SELECT * FROM events WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        )
        return [dict(r) for r in cur.fetchall()]

    def get_key_events(
        self,
        session_id: str,
        event_types: tuple[str, ...] = ("quest_update", "npc_interaction", "stat_change"),
    ) -> list[dict[str, Any]]:
        """Get notable events for session summaries."""
        placeholders = ",".join("?" for _ in event_types)
        cur = self._con.execute(
            f"SELECT * FROM events WHERE session_id = ? AND event_type IN ({placeholders}) "
            f"ORDER BY id",
            (session_id, *event_types),
        )
        return [dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Decision log
    # ------------------------------------------------------------------

    def record_decision(
        self,
        session_id: str,
        event_id: int | None,
        request: dict[str, Any],
        response: dict[str, Any],
        prediction: dict[str, Any] | None = None,
    ) -> int:
        """Record an LLM decision. Returns decision_id."""
        cur = self._con.execute(
            "INSERT INTO decision_log (session_id, event_id, request_json, response_json, prediction_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                session_id,
                event_id,
                json.dumps(request, default=str),
                json.dumps(response, default=str),
                json.dumps(prediction, default=str) if prediction else None,
            ),
        )
        self._con.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def update_decision_outcome(
        self,
        decision_id: int,
        outcome: dict[str, Any],
        surprise: bool = False,
        lesson: str | None = None,
    ) -> None:
        self._con.execute(
            "UPDATE decision_log SET outcome_json = ?, surprise_detected = ?, lesson_text = ? "
            "WHERE id = ?",
            (json.dumps(outcome, default=str), int(surprise), lesson, decision_id),
        )
        self._con.commit()

    def get_session_decisions(
        self,
        session_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        cur = self._con.execute(
            "SELECT * FROM decision_log WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        )
        return [dict(r) for r in cur.fetchall()]

    def get_lessons(
        self,
        session_id: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get decisions where surprises were detected and lessons learned."""
        if session_id:
            cur = self._con.execute(
                "SELECT * FROM decision_log WHERE session_id = ? AND surprise_detected = 1 "
                "ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            )
        else:
            cur = self._con.execute(
                "SELECT * FROM decision_log WHERE surprise_detected = 1 ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        return [dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def session_event_count(self, session_id: str) -> int:
        return self._con.execute(
            "SELECT COUNT(*) FROM events WHERE session_id = ?", (session_id,)
        ).fetchone()[0]

    def total_events(self) -> int:
        return self._con.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def total_sessions(self) -> int:
        return self._con.execute("SELECT COUNT(*) FROM game_sessions").fetchone()[0]


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()
