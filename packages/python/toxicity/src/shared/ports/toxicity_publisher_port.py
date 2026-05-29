from __future__ import annotations

from typing import Protocol
from features.score_toxicity.types import ToxicityScores

class ToxicityPublisherPort(Protocol):
    def publish_flagged(
        self, trace_id: str, span_id: str, score: float, scores: ToxicityScores
    ) -> None:
        ...
