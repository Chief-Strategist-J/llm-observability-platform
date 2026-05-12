"""Core instrumentation and sampled enrichment logic."""

from __future__ import annotations

import hashlib
import random
from dataclasses import asdict

from python_shared.types.llm_observability import PriceCard, TokenUsage
from python_shared.utils.pricing import compute_cost_usd

from .types import LLMSpanRecord


def should_sample(rate: float = 0.01) -> bool:
    return random.random() < rate


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def build_span_record(
    *,
    model: str,
    prompt: str,
    prompt_tokens: int,
    completion_tokens: int,
    finish_reason: str,
    ttft_ms: float,
    total_ms: float,
    price_card: PriceCard,
    sample_rate: float = 0.01,
) -> dict[str, object]:
    sampled = should_sample(sample_rate)
    usage = TokenUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
    record = LLMSpanRecord(
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        finish_reason=finish_reason,
        latency_ttft_ms=ttft_ms,
        latency_total_ms=total_ms,
        cost_usd=compute_cost_usd(usage, price_card),
        sampled=sampled,
        prompt_hash=prompt_hash(prompt) if sampled else None,
    )
    return asdict(record)
