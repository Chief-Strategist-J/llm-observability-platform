from __future__ import annotations

from typing import Protocol


class SentencizerPort(Protocol):
    def split(self, text: str, min_words: int) -> list[str]: ...
