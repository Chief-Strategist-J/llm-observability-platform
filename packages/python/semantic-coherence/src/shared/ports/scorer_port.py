from __future__ import annotations

from typing import Protocol


class ScorerPort(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def model_id(self) -> str: ...

    def compute(
        self,
        prompt_embedding: list[float],
        response_embedding: list[float],
    ) -> float: ...
