"""MemoryManager - unified facade across all four memory tiers.

Constructs the four backends (short, episodic, semantic, long) with their
default persistence paths under `C:/Dev/.shared/state/` and exposes them
as attributes the reasoning engine + tools can use directly. Tests can
disable persistence by passing `persist=False`.

Tier responsibilities:
  short      - per-session scratch chain-of-thought (in-memory only)
  episodic   - per-session event log (JSONL, one file per session)
  semantic   - world facts / NPC reputations / flags (single JSON file)
  long       - free-text recall (ChromaDB vector store, see long_term.py)
"""
from __future__ import annotations

from pathlib import Path

from .episodic import EpisodicMemory
from .long_term import LongTermMemory
from .semantic import SemanticMemory
from .short_term import ShortTermMemory


class MemoryManager:
    def __init__(self, persist: bool = True, state_root: Path | None = None) -> None:
        root = state_root or Path("C:/Dev/.shared/state")
        self.short = ShortTermMemory()
        self.episodic = EpisodicMemory(root=root / "episodic", persist=persist)
        self.semantic = SemanticMemory(path=root / "semantic.json", persist=persist)
        # LongTermMemory is force_dict=True when not persisting so tests
        # don't try to spin up chromadb.
        self.long = LongTermMemory(force_dict=not persist, path=root / "chroma")
