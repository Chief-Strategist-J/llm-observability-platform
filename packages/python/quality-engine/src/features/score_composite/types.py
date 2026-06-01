from __future__ import annotations

from pydantic import BaseModel, Field

class CompositeScoreInput(BaseModel):
    trace_id: str
    span_id: str
    coherence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    faithfulness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    toxicity_score: float | None = Field(default=None, ge=0.0, le=1.0)
    perplexity: float | None = Field(default=None, ge=0.0)
    perplexity_baseline: float = Field(default=2.0, ge=0.0)
    use_literal_formula: bool = False

class CompositeScoreResult(BaseModel):
    trace_id: str
    span_id: str
    composite_score: float | None
    quality_skipped_reason: str | None
    active_weights: dict[str, float]
    raw_contributions: dict[str, float]
