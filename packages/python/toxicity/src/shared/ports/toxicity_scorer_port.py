from __future__ import annotations

from typing import Protocol
from features.score_toxicity.types import ToxicityScores

class ToxicityScorerPort(Protocol):
    def tokenize(self, text: str) -> list[int]:
        ...

    def score_token_ids(self, token_ids: list[int]) -> ToxicityScores:
        ...
