from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()

class ReviewQueueItem(BaseModel):
    span_id: str
    trace_id: str
    model: str
    endpoint: str
    prompt_type: str
    response_language: str
    composite_score: float | None = None
    coherence_score: float | None = None
    toxicity_score: float | None = None
    faithfulness_score: float | None = None
    perplexity_score: float | None = None
    quality_flags: list[str] = Field(default_factory=list)
    skipped_reason: str | None = None
    review_status: str
    reviewed_at: datetime | None = None
    scored_at: datetime

class ReviewUpdateRequest(BaseModel):
    review_status: str

class ReviewUpdateResponse(BaseModel):
    span_id: str
    review_status: str
    reviewed_at: datetime

@router.get("/v1/review/queue", response_model=list[ReviewQueueItem])
def get_review_queue(
    request: Request,
    status: str = Query(default="pending")
) -> Any:
    repo = request.app.state.repo
    rows = repo.get_review_queue(status)
    return [
        ReviewQueueItem(
            span_id=r.span_id,
            trace_id=r.trace_id,
            model=r.model,
            endpoint=r.endpoint,
            prompt_type=r.prompt_type,
            response_language=r.response_language,
            composite_score=r.composite_score,
            coherence_score=r.coherence_score,
            toxicity_score=r.toxicity_score,
            faithfulness_score=r.faithfulness_score,
            perplexity_score=r.perplexity_score,
            quality_flags=r.quality_flags,
            skipped_reason=r.skipped_reason,
            review_status=r.review_status,
            reviewed_at=r.reviewed_at,
            scored_at=r.scored_at,
        )
        for r in rows
    ]

@router.post("/v1/review/{span_id}", response_model=ReviewUpdateResponse)
def submit_review(
    span_id: str,
    body: ReviewUpdateRequest,
    request: Request
) -> Any:
    repo = request.app.state.repo
    reviewed_at = datetime.now(timezone.utc)
    updated = repo.update_review_status(span_id, body.review_status, reviewed_at)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Span quality record with id '{span_id}' not found")
    return ReviewUpdateResponse(
        span_id=span_id,
        review_status=body.review_status,
        reviewed_at=reviewed_at,
    )
