from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class ToxicityInput:
    text: str

@dataclass(frozen=True)
class ToxicityScores:
    toxicity: float
    severe_toxicity: float
    obscene: float
    threat: float
    insult: float
    identity_hate: float

@dataclass(frozen=True)
class ToxicityResult:
    scores: ToxicityScores
    long_response_strategy: str
