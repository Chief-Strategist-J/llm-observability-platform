from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from features.score_semantic_coherence.service import score_semantic_coherence
from features.score_semantic_coherence.types import CoherenceInput, PromptType


router = APIRouter()


class ScoreRequest(BaseModel):
    trace_id: str
    span_id: str
    prompt_type: PromptType
    pii_detected: bool
    prompt_embedding: list[float] | None = None
    response_embedding: list[float] | None = None
    scorers: list[str] | None = None
    primary_scorer: str = "minilm"


class ScorerOutputSchema(BaseModel):
    scorer_name: str
    scorer_model: str
    score: float | None
    label: str | None
    skipped: bool
    skip_reason: str | None


class ScoreResponse(BaseModel):
    trace_id: str
    span_id: str
    prompt_type: PromptType
    skipped: bool
    skip_reason: str | None
    primary: ScorerOutputSchema | None
    all_scores: list[ScorerOutputSchema]


@router.post("/v1/score/semantic-coherence", response_model=ScoreResponse)
def score_endpoint(body: ScoreRequest, request: Request) -> Any:
    registry = request.app.state.scorer_registry
    embedding_store = request.app.state.embedding_store

    prompt_emb = body.prompt_embedding
    response_emb = body.response_embedding

    if prompt_emb is None or response_emb is None:
        fetched_prompt, fetched_response = embedding_store.fetch_embeddings(
            body.trace_id, body.span_id
        )
        if prompt_emb is None:
            prompt_emb = fetched_prompt
        if response_emb is None:
            response_emb = fetched_response

    selected_names = body.scorers
    if selected_names:
        scorers = [registry.get(n) for n in selected_names if registry.get(n)]
        if not scorers:
            raise HTTPException(
                status_code=400,
                detail=f"None of the requested scorers are registered: {selected_names}",
            )
    else:
        scorers = registry.all()

    coherence_input = CoherenceInput(
        prompt_type=body.prompt_type,
        pii_detected=body.pii_detected,
        prompt_embedding=prompt_emb,
        response_embedding=response_emb,
    )

    result = score_semantic_coherence(
        input=coherence_input,
        scorers=scorers,
        primary_scorer_name=body.primary_scorer,
    )

    primary_schema = (
        ScorerOutputSchema(
            scorer_name=result.primary.scorer_name,
            scorer_model=result.primary.scorer_model,
            score=result.primary.score,
            label=result.primary.label,
            skipped=result.primary.skipped,
            skip_reason=result.primary.skip_reason,
        )
        if result.primary
        else None
    )

    all_scores_schema = [
        ScorerOutputSchema(
            scorer_name=s.scorer_name,
            scorer_model=s.scorer_model,
            score=s.score,
            label=s.label,
            skipped=s.skipped,
            skip_reason=s.skip_reason,
        )
        for s in result.all_scores
    ]

    return ScoreResponse(
        trace_id=body.trace_id,
        span_id=body.span_id,
        prompt_type=result.prompt_type,
        skipped=result.skipped,
        skip_reason=result.skip_reason,
        primary=primary_schema,
        all_scores=all_scores_schema,
    )
