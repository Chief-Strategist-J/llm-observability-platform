from __future__ import annotations

from typing import Protocol

class NliScorerPort(Protocol):
    @property
    def model_id(self) -> str:
        ...

    @property
    def device_name(self) -> str:
        ...

    def count_tokens(self, text: str) -> int:
        ...

    def split_context_by_tokens(self, text: str, max_tokens: int = 400) -> list[str]:
        ...

    def score_pairs(
        self,
        pairs: list[tuple[str, str]],
        temperature: float = 1.5,
        batch_size: int = 8,
    ) -> list[tuple[float, float, float]]:
        ...
