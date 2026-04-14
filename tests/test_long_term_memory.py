"""LongTermMemory tests.

Forces the in-memory dict backend so tests run without chromadb installed.
A separate integration test path (skipped if chromadb is missing) covers
the chroma backend with a tmp_path collection.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from director_hub.memory.long_term import LongTermMemory


def test_dict_backend_index_and_search():
    mem = LongTermMemory(force_dict=True)
    assert mem.backend_name == "dict"
    mem.index({"text": "the goblin attacks the player"})
    mem.index({"text": "the player drinks a healing potion"})
    mem.index({"text": "an owl hoots in the distance"})
    results = mem.search("goblin", k=5)
    assert len(results) == 1
    assert "goblin" in str(results[0]).lower()


def test_dict_backend_search_returns_top_k():
    mem = LongTermMemory(force_dict=True)
    for i in range(10):
        mem.index({"text": f"event {i}: the player took an action"})
    results = mem.search("player", k=3)
    assert len(results) == 3


def test_dict_backend_empty_search():
    mem = LongTermMemory(force_dict=True)
    assert mem.search("nothing", k=5) == []


def test_dict_backend_count_and_reset():
    mem = LongTermMemory(force_dict=True)
    mem.index({"text": "a"})
    mem.index({"text": "b"})
    assert mem.count() == 2
    mem.reset()
    assert mem.count() == 0


def test_facade_falls_back_to_dict_when_chroma_unavailable(tmp_path: Path):
    """Even when force_dict is False, if chromadb isn't installed the
    facade should silently fall back to DictBackend rather than crash."""
    mem = LongTermMemory(path=tmp_path / "chroma_test")
    # backend_name is either 'chroma' (if chromadb is installed) or 'dict'
    # (the fallback). Both are valid; the point is that no exception escaped.
    assert mem.backend_name in ("chroma", "dict")
    mem.index({"text": "smoke"})
    assert mem.count() >= 1


try:
    import chromadb  # noqa: F401

    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False


@pytest.mark.skipif(not _CHROMA_AVAILABLE, reason="chromadb not installed")
def test_chroma_backend_round_trip(tmp_path: Path):
    """When chromadb IS installed, exercise the full vector-search path
    against a fresh persistent collection in tmp_path."""
    mem = LongTermMemory(path=tmp_path / "chroma_real")
    if mem.backend_name != "chroma":
        pytest.skip("chromadb installed but backend selection landed on dict")
    mem.index({"text": "the player slays a dragon", "biome": "mountain"})
    mem.index({"text": "the player picks a wildflower", "biome": "meadow"})
    mem.index({"text": "the player crafts a sword", "biome": "forge"})
    results = mem.search("dragon combat victory", k=2)
    assert len(results) >= 1
    assert any("dragon" in str(r).lower() for r in results)
