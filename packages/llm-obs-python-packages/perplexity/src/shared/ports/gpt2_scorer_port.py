from __future__ import annotations

from typing import Protocol


class Gpt2ScorerPort(Protocol):
    def is_available(self) -> bool: ...

    def compute(self, response_text: str) -> float | None: ...

    def compute_with_token_count(self, response_text: str) -> tuple[float | None, int]: ...

