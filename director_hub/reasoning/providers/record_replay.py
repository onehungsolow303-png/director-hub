"""Record/replay decorator for any ReasoningProvider.

The agentic AI is non-deterministic by nature — Anthropic's Messages API does
not expose a `seed` parameter, so even with `temperature=0` two identical
requests can return slightly different narratives. That's fatal for
golden-test reproducibility, where we want a request to produce *byte-for-byte
identical* responses every time the eval suite runs.

This module provides the standard solution: cassette-based record/replay,
modeled after VCR.py / nock / polly.js. The wrapper sits between the
ReasoningEngine and the underlying provider:

    live    → passthrough (default; no caching)
    record  → call the backing provider, save the response keyed by a
              stable hash of the request, then return the response
    replay  → look up the response by hash; raise CassetteMiss if absent
              (the backing provider is NEVER called in replay mode, so
              tests can run offline against cached fixtures)

Cassette key: SHA256 of canonical-JSON action_request with `session_id`
stripped (session IDs are per-test and don't affect LLM behavior). All
other fields — player_input, actor_stats, scene_context, recent_history —
contribute to the hash, so changing any of them invalidates the cassette
and forces a re-record.

Cassette format on disk: one JSON file per cassette under `cassette_dir/`,
named `{first 16 hex chars of hash}.json` for human browsability. The full
hash is stored inside the file so collisions are detected.

    {
      "hash": "<full sha256>",
      "request": {... canonical request ...},
      "response": {... full DecisionPayload-shaped dict ...},
      "model": "claude-haiku-4-5",
      "recorded_at": "2026-04-08T06:55:00Z"
    }

Wrap any provider:

    from director_hub.reasoning.providers.record_replay import (
        RecordReplayProvider, ReplayMode,
    )
    from director_hub.reasoning.providers.anthropic import AnthropicProvider

    backing = AnthropicProvider(model="claude-haiku-4-5")
    provider = RecordReplayProvider(
        backing=backing,
        mode=ReplayMode.RECORD,
        cassette_dir=Path("director_hub/evals/cassettes"),
    )
    decision = provider.interpret(action_request)  # writes a cassette

The next run with mode=REPLAY against the same cassette_dir + same
action_request will return the cached `decision` without ever calling
Anthropic — true deterministic test runs.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from .base import ReasoningProvider

logger = logging.getLogger(__name__)


class ReplayMode(StrEnum):
    LIVE = "live"  # passthrough — no cassette interaction
    RECORD = "record"  # call backing provider + write cassette
    REPLAY = "replay"  # read cassette only; never call backing provider


class CassetteMiss(Exception):
    """Raised in REPLAY mode when no cassette matches the request hash."""


class RecordReplayProvider(ReasoningProvider):
    """Decorator that adds record/replay caching around any backing provider."""

    name = "record_replay"

    def __init__(
        self,
        backing: ReasoningProvider,
        mode: ReplayMode | str,
        cassette_dir: Path | str,
    ) -> None:
        self._backing = backing
        self._mode = ReplayMode(mode) if isinstance(mode, str) else mode
        self._cassette_dir = Path(cassette_dir)
        if self._mode in (ReplayMode.RECORD, ReplayMode.REPLAY):
            # Make sure the directory exists for record mode; for replay
            # mode a missing directory will simply produce CassetteMiss
            # on every request, which is the right failure mode (loud).
            self._cassette_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"[RecordReplay] mode={self._mode.value} "
            f"cassette_dir={self._cassette_dir} "
            f"backing={getattr(self._backing, 'name', type(self._backing).__name__)}"
        )

    @property
    def mode(self) -> ReplayMode:
        return self._mode

    @property
    def cassette_dir(self) -> Path:
        return self._cassette_dir

    @property
    def is_real(self) -> bool:
        # The decorator inherits realness from its backing provider in
        # LIVE and RECORD modes (a real call is happening). In REPLAY
        # mode the response is canned, so it's not "real" in the sense
        # the deterministic_fallback flag uses — but the cached response
        # CAME from a real provider originally, so it's also not stub.
        # We treat replay as real because the wire data is identical to
        # what the live provider would have returned, which is what the
        # deterministic_fallback flag is signaling about.
        return self._backing.is_real

    def interpret(self, action_request: dict[str, Any]) -> dict[str, Any]:
        if self._mode == ReplayMode.LIVE:
            return self._backing.interpret(action_request)

        cassette_key = self._hash_request(action_request)
        cassette_path = self._cassette_path(cassette_key)

        if self._mode == ReplayMode.REPLAY:
            return self._load_cassette(cassette_path, cassette_key)

        # RECORD mode: try the backing provider first; on success, persist.
        # If the backing provider fails, propagate the exception — we don't
        # want to silently miss a recording opportunity.
        decision = self._backing.interpret(action_request)
        self._save_cassette(
            cassette_path=cassette_path,
            cassette_key=cassette_key,
            request=action_request,
            response=decision,
        )
        return decision

    # ─────────────────────────────────────────────────────────────────
    # Cassette I/O
    # ─────────────────────────────────────────────────────────────────

    def _cassette_path(self, cassette_key: str) -> Path:
        # First 16 hex chars are the filename for human browsability;
        # the full hash is stored inside the file as a collision check.
        return self._cassette_dir / f"{cassette_key[:16]}.json"

    def _save_cassette(
        self,
        *,
        cassette_path: Path,
        cassette_key: str,
        request: dict[str, Any],
        response: dict[str, Any],
    ) -> None:
        cassette = {
            "hash": cassette_key,
            "request": _canonical_request(request),
            "response": response,
            "model": getattr(self._backing, "_model", None) or getattr(self._backing, "name", None),
            "recorded_at": datetime.now(UTC).isoformat(),
        }
        cassette_path.write_text(
            json.dumps(cassette, indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        logger.info(f"[RecordReplay] wrote cassette {cassette_path.name}")

    def _load_cassette(
        self,
        cassette_path: Path,
        cassette_key: str,
    ) -> dict[str, Any]:
        if not cassette_path.exists():
            raise CassetteMiss(
                f"no cassette at {cassette_path} for request hash {cassette_key}. "
                "Re-record with mode=record to capture this scenario."
            )
        try:
            cassette = json.loads(cassette_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise CassetteMiss(f"cassette at {cassette_path} could not be loaded: {e}") from e

        # Defend against truncated filename collisions: the file is named
        # by the first 16 hex chars of the hash but stores the full hash.
        # Different requests that happen to share a 16-char prefix would
        # collide on disk; we detect that here and raise rather than
        # serve the wrong response.
        stored_hash = cassette.get("hash")
        if stored_hash != cassette_key:
            raise CassetteMiss(
                f"cassette hash collision at {cassette_path}: "
                f"stored {stored_hash!r}, requested {cassette_key!r}"
            )

        response = cassette.get("response")
        if not isinstance(response, dict):
            raise CassetteMiss(f"cassette at {cassette_path} has no response dict")
        return response

    # ─────────────────────────────────────────────────────────────────
    # Hashing
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _hash_request(action_request: dict[str, Any]) -> str:
        """Return a stable SHA256 of the request, ignoring session_id.

        Stability matters: dicts in Python preserve insertion order so
        json.dumps without sort_keys would produce different hashes for
        semantically identical requests assembled in different orders.
        We sort keys recursively via json.dumps(sort_keys=True).

        session_id is stripped because it's per-test/per-conversation
        and changes every run; including it would make every cassette
        a one-shot.
        """
        canonical = _canonical_request(action_request)
        blob = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _canonical_request(action_request: dict[str, Any]) -> dict[str, Any]:
    """Drop fields that don't affect LLM behavior so the hash stays stable.

    Currently strips:
        - session_id (per-conversation, varies every test)
        - schema_version (contract version, doesn't affect responses)
    """
    return {k: v for k, v in action_request.items() if k not in ("session_id", "schema_version")}
