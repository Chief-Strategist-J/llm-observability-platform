from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from features.score_perplexity.service import score_perplexity
from features.score_perplexity.types import PerplexityInput


router = APIRouter()


class ScoreRequest(BaseModel):
    trace_id: str
    span_id: str
    response_text: str
    completion_tokens: int
    prompt_type: Literal["chat", "code", "rag", "classification"]
    token_logprobs: list[float] | None = None
    finish_reason: str | None = None


class ScoreResponse(BaseModel):
    trace_id: str
    span_id: str
    perplexity: float | None
    score: float | None
    weight: float
    skipped: bool
    skip_reason: str | None
    high_perplexity_flag: bool
    prompt_type: str
    scorer_used: str | None


@router.post("/v1/score/perplexity", response_model=ScoreResponse)
def score_endpoint(body: ScoreRequest, request: Request) -> Any:
    logprobs_scorer = request.app.state.logprobs_scorer
    gpt2_scorer = request.app.state.gpt2_scorer

    perp_input = PerplexityInput(
        response_text=body.response_text,
        completion_tokens=body.completion_tokens,
        prompt_type=body.prompt_type,
        token_logprobs=body.token_logprobs,
        finish_reason=body.finish_reason,
    )

    result = score_perplexity(
        input=perp_input,
        logprobs_scorer=logprobs_scorer,
        gpt2_scorer=gpt2_scorer,
        trace_id=body.trace_id,
        span_id=body.span_id,
    )

    return ScoreResponse(
        trace_id=body.trace_id,
        span_id=body.span_id,
        perplexity=result.perplexity,
        score=result.score,
        weight=result.weight,
        skipped=result.skipped,
        skip_reason=result.skip_reason,
        high_perplexity_flag=result.high_perplexity_flag,
        prompt_type=result.prompt_type,
        scorer_used=result.scorer_used,
    )
