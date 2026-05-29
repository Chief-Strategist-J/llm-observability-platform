from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class ToxicityInput:
    response_text: str

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
    score: float | None
    flagged: bool
    flag: str | None
    skipped: bool
    skip_reason: str | None
    scores: ToxicityScores | None
