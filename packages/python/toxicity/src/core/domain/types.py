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
    long_response_strategy: str | None = None
    # Flagging fields — populated when publisher is wired in
    score: float | None = None
    flagged: bool = False
    flag: str | None = None
    skipped: bool = False
    skip_reason: str | None = None
