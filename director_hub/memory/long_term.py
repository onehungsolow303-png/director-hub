"""Long-term memory - vector store backed by ChromaDB when available.

Spec §14 follow-up #3. Two backends:

- ChromaBackend: real vector search via chromadb's PersistentClient. Each
  Director Hub instance maintains its own collection at .shared/state/
  chroma/ — across restarts the index is preserved. Uses chromadb's
  default sentence-transformer embedder so no API key is required.
- DictBackend: in-memory dict with substring matching. The fallback when
  chromadb isn't installed (or fails to import on a minimal venv).

The public LongTermMemory class auto-detects which backend to use at
construction. Pass `force_dict=True` to skip chromadb in tests.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CHROMA_PATH = Path("C:/Dev/.shared/state/chroma")


class _DictBackend:
    """In-memory substring search. Always available, never persistent."""

    name = "dict"

    def __init__(self) -> None:
        self._docs: list[dict[str, Any]] = []

    def index(self, doc: dict[str, Any]) -> None:
        self._docs.append(doc)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        q = query.lower()
        return [d for d in self._docs if q in str(d).lower()][:k]

    def count(self) -> int:
        return len(self._docs)

    def reset(self) -> None:
        self._docs.clear()


class _ChromaBackend:
    """ChromaDB-backed vector store with sentence-transformer embeddings.

    Construction may fail with ImportError if chromadb isn't installed,
    or with RuntimeError if the persistent path can't be created. Callers
    that want a guaranteed-working backend should catch and fall back.
    """

    name = "chroma"

    def __init__(
        self, path: Path = DEFAULT_CHROMA_PATH, collection: str = "director_hub_ltm"
    ) -> None:
        try:
            import chromadb  # noqa: F401
        except ImportError as e:
            raise ImportError(
                f"chromadb not installed: {e}. Run `pip install -e .[chroma]`."
            ) from e

        path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(path))
        # get_or_create_collection makes us idempotent across restarts
        self._collection = self._client.get_or_create_collection(name=collection)
        self._next_id = self._collection.count()

    def index(self, doc: dict[str, Any]) -> None:
        text = doc.get("text") or str(doc)
        self._collection.add(
            ids=[f"doc_{self._next_id}"],
            documents=[text],
            metadatas=[{k: v for k, v in doc.items() if isinstance(v, (str, int, float, bool))}],
        )
        self._next_id += 1

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        if self._collection.count() == 0:
            return []
        results = self._collection.query(query_texts=[query], n_results=k)
        # results is a dict of lists of lists; flatten to a list of doc dicts
        out: list[dict[str, Any]] = []
        docs = (results.get("documents") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]
        for text, meta in zip(docs, metas, strict=False):
            entry = {"text": text}
            if meta:
                entry.update(meta)
            out.append(entry)
        return out

    def count(self) -> int:
        return self._collection.count()

    def reset(self) -> None:
        self._client.delete_collection(self._collection.name)
        self._collection = self._client.get_or_create_collection(name=self._collection.name)
        self._next_id = 0


class LongTermMemory:
    """Vector-store memory facade. Routes to ChromaBackend when chromadb
    is available, DictBackend otherwise."""

    def __init__(self, force_dict: bool = False, path: Path | None = None) -> None:
        if force_dict:
            self._backend: Any = _DictBackend()
            return
        try:
            self._backend = _ChromaBackend(path=path or DEFAULT_CHROMA_PATH)
            logger.info("[LongTermMemory] using ChromaBackend at %s", path or DEFAULT_CHROMA_PATH)
        except (ImportError, RuntimeError) as e:
            logger.warning("[LongTermMemory] ChromaBackend unavailable (%s); using DictBackend.", e)
            self._backend = _DictBackend()

    @property
    def backend_name(self) -> str:
        return self._backend.name

    def index(self, doc: dict[str, Any]) -> None:
        self._backend.index(doc)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        return self._backend.search(query, k)

    def count(self) -> int:
        return self._backend.count()

    def reset(self) -> None:
        self._backend.reset()
