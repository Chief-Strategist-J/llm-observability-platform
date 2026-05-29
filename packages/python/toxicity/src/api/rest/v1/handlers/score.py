from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from features.score_toxicity.service import score_toxicity
from features.score_toxicity.types import ToxicityInput

router = APIRouter()

class ScoreRequest(BaseModel):
    trace_id: str
    span_id: str
    response_text: str

class ToxicityScoresSchema(BaseModel):
    toxicity: float
    severe_toxicity: float
    obscene: float
    threat: float
    insult: float
    identity_hate: float

class ScoreResponse(BaseModel):
    trace_id: str
    span_id: str
    score: float | None
    flagged: bool
    flag: str | None
    skipped: bool
    skip_reason: str | None
    scores: ToxicityScoresSchema | None

@router.post("/v1/score/toxicity", response_model=ScoreResponse)
def score_endpoint(body: ScoreRequest, request: Request) -> Any:
    scorer = request.app.state.toxicity_scorer
    publisher = request.app.state.toxicity_publisher

    toxicity_input = ToxicityInput(response_text=body.response_text)

    result = score_toxicity(
        input=toxicity_input,
        scorer=scorer,
        publisher=publisher,
        trace_id=body.trace_id,
        span_id=body.span_id,
    )

    schema_scores = None
    if result.scores:
        schema_scores = ToxicityScoresSchema(
            toxicity=result.scores.toxicity,
            severe_toxicity=result.scores.severe_toxicity,
            obscene=result.scores.obscene,
            threat=result.scores.threat,
            insult=result.scores.insult,
            identity_hate=result.scores.identity_hate,
        )

    return ScoreResponse(
        trace_id=body.trace_id,
        span_id=body.span_id,
        score=result.score,
        flagged=result.flagged,
        flag=result.flag,
        skipped=result.skipped,
        skip_reason=result.skip_reason,
        scores=schema_scores,
    )
