from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


PromptType = Literal["chat", "code", "rag", "classification"]
FinishReason = Literal["stop", "length", "content_filter", "tool_calls"]


@dataclass(frozen=True)
class QualityScoreRow:
    """Row written to PostgreSQL quality_scores table after scoring.
    Lives in shared/types/ to avoid coupling ports → handler types.
    """
    span_id: str
    trace_id: str
    model: str
    endpoint: str
    prompt_type: PromptType
    response_language: str
    composite_score: float | None
    coherence_score: float | None
    toxicity_score: float | None
    faithfulness_score: float | None
    perplexity_score: float | None
    quality_flags: list[str]
    skipped_reason: str | None
    scored_at: datetime
