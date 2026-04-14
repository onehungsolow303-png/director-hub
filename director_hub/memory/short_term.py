"""Short-term memory - ongoing chain-of-thought for the current session. STUB."""

from __future__ import annotations


class ShortTermMemory:
    def __init__(self) -> None:
        self._buffer: list[str] = []

    def add(self, item: str) -> None:
        self._buffer.append(item)

    def recent(self, n: int = 10) -> list[str]:
        return self._buffer[-n:]

    def clear(self) -> None:
        self._buffer.clear()
