"""Semantic memory - facts about the world.

Disk-backed key-value store. Each key→value pair persists to a single
JSON file at `C:/Dev/.shared/state/semantic.json` by default. Reads are
served from an in-memory dict that's loaded on construction.

This is the right backend for things that need to survive across restarts
but don't need vector search: NPC reputations, faction states, world
flags, named-entity beliefs, etc. Use LongTermMemory's ChromaDB backend
for free-text recall.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_SEMANTIC_PATH = Path("C:/Dev/.shared/state/semantic.json")


class SemanticMemory:
    def __init__(
        self,
        path: Path | None = None,
        persist: bool = True,
    ) -> None:
        self._path = path or DEFAULT_SEMANTIC_PATH
        self._persist = persist
        self._facts: dict[str, Any] = {}
        if self._persist and self._path.exists():
            try:
                self._facts = json.loads(self._path.read_text(encoding="utf-8"))
                if not isinstance(self._facts, dict):
                    logger.warning(
                        "[SemanticMemory] %s is not a dict; starting fresh",
                        self._path,
                    )
                    self._facts = {}
            except (OSError, json.JSONDecodeError) as e:
                logger.warning("[SemanticMemory] failed to load %s: %s", self._path, e)
                self._facts = {}

    def set(self, key: str, value: Any) -> None:
        self._facts[key] = value
        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        return self._facts.get(key, default)

    def delete(self, key: str) -> bool:
        if key not in self._facts:
            return False
        del self._facts[key]
        self._save()
        return True

    def all(self) -> dict[str, Any]:
        return dict(self._facts)

    def keys(self) -> list[str]:
        return list(self._facts.keys())

    def wipe(self) -> None:
        """Clear in-memory and delete the on-disk file."""
        self._facts.clear()
        if self._persist and self._path.exists():
            self._path.unlink()

    def _save(self) -> None:
        if not self._persist:
            return
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(self._facts, indent=2, default=str),
                encoding="utf-8",
            )
        except OSError as e:
            logger.warning("[SemanticMemory] persist failed: %s", e)
