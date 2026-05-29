from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from features.score_faithfulness.service import score_faithfulness
from features.score_faithfulness.types import FaithfulnessInput


router = APIRouter()


class ScoreRequest(BaseModel):
    trace_id: str
    span_id: str
    response_text: str
    completion_tokens: int
    rag_context: str | None = None
    finish_reason: str | None = None


class SentenceResultSchema(BaseModel):
    sentence: str
    label: str
    entailment_prob: float


class ScoreResponse(BaseModel):
    trace_id: str
    span_id: str
    score: float | None
    skipped: bool
    skip_reason: str | None
    total_qualifying: int | None
    entailed_count: int | None
    sentence_results: list[SentenceResultSchema]


@router.post("/v1/score/faithfulness", response_model=ScoreResponse)
def score_endpoint(body: ScoreRequest, request: Request) -> Any:
    nli_scorer = request.app.state.nli_scorer
    sentencizer = request.app.state.sentencizer

    faith_input = FaithfulnessInput(
        rag_context=body.rag_context,
        response_text=body.response_text,
        completion_tokens=body.completion_tokens,
        finish_reason=body.finish_reason,
    )

    result = score_faithfulness(
        input=faith_input,
        sentencizer=sentencizer,
        nli_scorer=nli_scorer,
    )

    return ScoreResponse(
        trace_id=body.trace_id,
        span_id=body.span_id,
        score=result.score,
        skipped=result.skipped,
        skip_reason=result.skip_reason,
        total_qualifying=result.total_qualifying,
        entailed_count=result.entailed_count,
        sentence_results=[
            SentenceResultSchema(
                sentence=r.sentence,
                label=r.label,
                entailment_prob=r.entailment_prob,
            )
            for r in result.sentence_results
        ],
    )
