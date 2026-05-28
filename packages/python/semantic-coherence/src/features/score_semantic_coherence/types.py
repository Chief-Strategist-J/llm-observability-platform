from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PromptType = Literal["chat", "code", "rag", "classification"]


@dataclass(frozen=True)
class CoherenceInput:
    prompt_type: PromptType
    pii_detected: bool
    prompt_embedding: list[float] | None = None
    response_embedding: list[float] | None = None


@dataclass(frozen=True)
class ScorerOutput:
    scorer_name: str
    scorer_model: str
    score: float | None
    label: str | None
    skipped: bool
    skip_reason: str | None


@dataclass(frozen=True)
class CoherenceResult:
    prompt_type: PromptType
    skipped: bool
    skip_reason: str | None
    primary: ScorerOutput | None
    all_scores: list[ScorerOutput]
