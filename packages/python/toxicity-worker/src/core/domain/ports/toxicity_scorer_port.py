from __future__ import annotations

from abc import ABC, abstractmethod
from core.domain.types import ToxicityScores

class ToxicityScorerPort(ABC):
    @abstractmethod
    def tokenize(self, text: str) -> list[int]:
        pass

    @abstractmethod
    def score_token_ids(self, token_ids: list[int]) -> ToxicityScores:
        pass

    def warmup(self) -> None:
        pass

