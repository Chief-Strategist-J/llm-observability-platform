"""Shared types for LLM observability."""

from dataclasses import dataclass
from typing import Literal

FinishReason = Literal["stop", "length", "content_filter", "tool_calls", "other"]


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int


@dataclass(slots=True)
class PriceCard:
    model: str
    input_price_per_token: float
    output_price_per_token: float
