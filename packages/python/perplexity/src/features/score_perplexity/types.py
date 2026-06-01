from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PromptType = Literal["chat", "code", "rag", "classification"]
ScorerUsed = Literal["provider_logprobs", "gpt2_onnx"] | None


@dataclass(frozen=True)
class PerplexityInput:
    response_text: str
    completion_tokens: int
    prompt_type: PromptType
    token_logprobs: list[float] | None = None
    finish_reason: str | None = None


@dataclass(frozen=True)
class PerplexityResult:
    perplexity: float | None
    score: float | None
    weight: float
    skipped: bool
    skip_reason: str | None
    high_perplexity_flag: bool
    prompt_type: PromptType
    scorer_used: ScorerUsed
