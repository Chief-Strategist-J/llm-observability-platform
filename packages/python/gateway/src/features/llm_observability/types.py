"""Feature-local types for LLM call spans."""

from dataclasses import dataclass


@dataclass(slots=True)
class LatencyBreakdown:
    ttft_ms: float
    total_ms: float


@dataclass(slots=True)
class LLMSpanRecord:
    model: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str
    latency_ttft_ms: float
    latency_total_ms: float
    cost_usd: float
    sampled: bool
    prompt_hash: str | None = None
