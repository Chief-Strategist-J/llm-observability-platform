from __future__ import annotations

import math

from features.score_perplexity.types import PerplexityInput, PromptType

MIN_COMPLETION_TOKENS: int = 10
HIGH_PERPLEXITY_MULTIPLIER: float = 3.0
WEIGHT_ACTIVE: float = 0.10
WEIGHT_SKIPPED: float = 0.00
BLOCKED_FINISH_REASONS: frozenset[str] = frozenset({"content_filter"})

_BASELINES: dict[PromptType, tuple[float, float]] = {
    "chat": (15.0, 35.0),
    "code": (8.0, 20.0),
    "rag": (12.0, 28.0),
    "classification": (6.0, 15.0),
}


def baseline_for(prompt_type: PromptType) -> tuple[float, float]:
    return _BASELINES[prompt_type]


def should_skip(input: PerplexityInput) -> tuple[bool, str | None]:
    if input.finish_reason in BLOCKED_FINISH_REASONS:
        return True, "finish_reason_blocked"
    if input.completion_tokens < MIN_COMPLETION_TOKENS:
        return True, "completion_tokens_too_few"
    return False, None


def compute_perplexity_from_logprobs(token_logprobs: list[float]) -> float:
    n = len(token_logprobs)
    return math.exp(-sum(token_logprobs) / n)


def is_high_perplexity(perplexity: float, prompt_type: PromptType) -> bool:
    _, baseline_high = baseline_for(prompt_type)
    return perplexity > HIGH_PERPLEXITY_MULTIPLIER * baseline_high


def normalize_contribution(perplexity: float, prompt_type: PromptType) -> float:
    baseline_low, baseline_high = baseline_for(prompt_type)
    log_perp = math.log(max(perplexity, 1.0))
    log_low = math.log(max(baseline_low, 1.0))
    log_high = math.log(max(baseline_high, 1.0))
    raw = 1.0 / log_perp if log_perp > 0 else 0.0
    high_contrib = 1.0 / log_low if log_low > 0 else 1.0
    low_contrib = 1.0 / log_high if log_high > 0 else 0.0
    rng = high_contrib - low_contrib
    if rng <= 0:
        return 0.0
    normalized = (raw - low_contrib) / rng
    return max(0.0, min(1.0, normalized))
