"""MemoryManager - unified facade across all four memory tiers. STUB."""
from __future__ import annotations

from .episodic import EpisodicMemory
from .long_term import LongTermMemory
from .semantic import SemanticMemory
from .short_term import ShortTermMemory


class MemoryManager:
    def __init__(self) -> None:
        self.short = ShortTermMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.long = LongTermMemory()
