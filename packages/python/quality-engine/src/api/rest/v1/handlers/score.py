from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from features.score_composite import score_composite, CompositeScoreInput

router = APIRouter()

class ScoreRequest(BaseModel):
    trace_id: str
    span_id: str
    coherence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    faithfulness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    toxicity_score: float | None = Field(default=None, ge=0.0, le=1.0)
    perplexity: float | None = Field(default=None, ge=0.0)
    perplexity_baseline: float = Field(default=2.0, ge=0.0)
    use_literal_formula: bool = False

class ScoreResponse(BaseModel):
    trace_id: str
    span_id: str
    composite_score: float | None
    quality_skipped_reason: str | None
    active_weights: dict[str, float]
    raw_contributions: dict[str, float]

@router.post("/v1/score/composite", response_model=ScoreResponse)
def score_endpoint(body: ScoreRequest, request: Request) -> Any:
    alert_publisher = request.app.state.alert_publisher
    inp = CompositeScoreInput(
        trace_id=body.trace_id,
        span_id=body.span_id,
        coherence_score=body.coherence_score,
        faithfulness_score=body.faithfulness_score,
        toxicity_score=body.toxicity_score,
        perplexity=body.perplexity,
        perplexity_baseline=body.perplexity_baseline,
        use_literal_formula=body.use_literal_formula,
    )
    result = score_composite(inp, alert_publisher)
    return ScoreResponse(
        trace_id=result.trace_id,
        span_id=result.span_id,
        composite_score=result.composite_score,
        quality_skipped_reason=result.quality_skipped_reason,
        active_weights=result.active_weights,
        raw_contributions=result.raw_contributions,
    )
