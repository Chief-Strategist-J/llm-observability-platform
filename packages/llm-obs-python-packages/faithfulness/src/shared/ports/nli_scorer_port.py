from __future__ import annotations

from typing import Protocol


class NliScorerPort(Protocol):
    @property
    def model_id(self) -> str: ...

    def score_pairs(
        self,
        pairs: list[tuple[str, str]],
    ) -> list[tuple[float, float, float]]: ...
