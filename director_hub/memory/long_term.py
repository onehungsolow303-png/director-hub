"""Long-term memory - vector-DB-backed RAG store.

SCAFFOLDING STUB. See spec §14 follow-up #3 (vector DB choice).
"""
from __future__ import annotations

from typing import Any


class LongTermMemory:
    def __init__(self) -> None:
        self._docs: list[dict[str, Any]] = []

    def index(self, doc: dict[str, Any]) -> None:
        self._docs.append(doc)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        return [d for d in self._docs if query.lower() in str(d).lower()][:k]
