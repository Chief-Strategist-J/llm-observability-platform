from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from core.domain.service import score_toxicity
from core.domain.types import ToxicityInput

router = APIRouter()


class ScoreRequest(BaseModel):
    text: str
    # Optional — when present the span is linked to the upstream trace context
    trace_id: str | None = None
    span_id: str | None = None


class ToxicityScoresSchema(BaseModel):
    toxicity: float
    severe_toxicity: float
    obscene: float
    threat: float
    insult: float
    identity_hate: float


class ScoreResponse(BaseModel):
    toxicity: float
    severe_toxicity: float
    obscene: float
    threat: float
    insult: float
    identity_hate: float
    long_response_strategy: str | None = None
    # Flagging fields — always present; flagged=False when publisher not wired
    score: float | None = None
    flagged: bool = False
    flag: str | None = None
    skipped: bool = False
    skip_reason: str | None = None


@router.post("/score", response_model=ScoreResponse, response_model_exclude_none=True)
def score_endpoint(body: ScoreRequest, request: Request) -> Any:
    scorer = request.app.state.toxicity_scorer
    publisher = getattr(request.app.state, "toxicity_publisher", None)

    # Also support upstream trace context from W3C traceparent header
    trace_id = body.trace_id
    span_id = body.span_id
    traceparent = request.headers.get("traceparent")
    if traceparent and not (trace_id and span_id):
        parts = traceparent.split("-")
        if len(parts) >= 3:
            trace_id = parts[1]
            span_id = parts[2]

    result = score_toxicity(
        input=ToxicityInput(text=body.text),
        scorer=scorer,
        trace_id=trace_id,
        span_id=span_id,
        publisher=publisher,
    )

    return ScoreResponse(
        toxicity=result.scores.toxicity,
        severe_toxicity=result.scores.severe_toxicity,
        obscene=result.scores.obscene,
        threat=result.scores.threat,
        insult=result.scores.insult,
        identity_hate=result.scores.identity_hate,
        long_response_strategy=result.long_response_strategy,
        score=result.score,
        flagged=result.flagged,
        flag=result.flag,
        skipped=result.skipped,
        skip_reason=result.skip_reason,
    )
