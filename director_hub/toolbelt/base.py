"""Tool ABC - every tool the brain can call implements this. STUB."""
from __future__ import annotations

import abc
from typing import Any


class Tool(abc.ABC):
    name: str = "tool"
    description: str = ""

    @abc.abstractmethod
    def call(self, **kwargs: Any) -> Any: ...
