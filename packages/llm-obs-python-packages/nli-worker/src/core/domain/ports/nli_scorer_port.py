from __future__ import annotations

from typing import Protocol

class NliScorerPort(Protocol):
    @property
    def default_model_id(self) -> str:
        ...

    @property
    def device_name(self) -> str:
        ...

    def count_tokens(self, text: str, model_id: str | None = None) -> int:
        ...

    def split_context_by_tokens(
        self,
        text: str,
        max_tokens: int = 400,
        model_id: str | None = None,
    ) -> list[str]:
        ...

    def score_pairs(
        self,
        pairs: list[tuple[str, str]],
        temperature: float = 1.5,
        batch_size: int | None = None,
        model_id: str | None = None,
    ) -> list[tuple[float, float, float]]:
        ...
