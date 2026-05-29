from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FaithfulnessInput:
    response_text: str
    completion_tokens: int
    rag_context: str | None = None
    finish_reason: str | None = None


@dataclass(frozen=True)
class SentenceResult:
    sentence: str
    label: str
    entailment_prob: float


@dataclass(frozen=True)
class FaithfulnessResult:
    score: float | None
    skipped: bool
    skip_reason: str | None
    sentence_results: list[SentenceResult]
    total_qualifying: int | None
    entailed_count: int | None
