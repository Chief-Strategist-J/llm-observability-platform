from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

# Re-export from shared so handler-internal code can use one import location
from shared.types.quality_score_row import QualityScoreRow, PromptType, FinishReason


@dataclass(frozen=True)
class SampledSpan:
    """Parsed payload consumed from llm.spans.sampled."""
    span_id: str
    trace_id: str
    model: str
    endpoint: str
    prompt_text: str
    response_text: str
    completion_tokens: int
    finish_reason: FinishReason
    prompt_tokens: int = 0
    rag_context: str | None = None
    prompt_embedding: list[float] | None = None
    response_embedding: list[float] | None = None
    provider_logprobs: list[float] | None = None
    scored_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class ScoreMap:
    """Available individual scores collected after all Temporal activities complete."""
    coherence: float | None = None
    toxicity: float | None = None
    faithfulness: float | None = None
    perplexity: float | None = None


INVARIANT_IDS = [
    "INV-Q-01",  # composite in [0, 1]
    "INV-Q-02",  # coherence in [0, 1] if present
    "INV-Q-03",  # toxicity in [0, 1] if present
    "INV-Q-04",  # faithfulness in [0, 1] if present
    "INV-Q-05",  # perplexity_score non-negative if present
    "INV-Q-06",  # at least one score present if composite is not null
    "INV-Q-07",  # toxicity always present (unless model unavailable)
]
