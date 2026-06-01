from __future__ import annotations

from typing import Protocol


class Gpt2ScorerPort(Protocol):
    def is_available(self) -> bool: ...

    def compute(self, response_text: str) -> float | None: ...
