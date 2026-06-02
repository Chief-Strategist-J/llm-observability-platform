from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Request
from pydantic import BaseModel

from core.domain.service import score_toxicity
from core.domain.types import ToxicityInput

router = APIRouter()

class ScoreRequest(BaseModel):
    text: str

class ScoreResponse(BaseModel):
    toxicity: float
    severe_toxicity: float
    obscene: float
    threat: float
    insult: float
    identity_hate: float
    long_response_strategy: str

@router.post("/score", response_model=ScoreResponse)
def score_endpoint(body: ScoreRequest, request: Request) -> Any:
    scorer = request.app.state.toxicity_scorer

    traceparent = request.headers.get("traceparent")
    trace_id = None
    span_id = None
    if traceparent:
        parts = traceparent.split("-")
        if len(parts) >= 3:
            trace_id = parts[1]
            span_id = parts[2]

    toxicity_input = ToxicityInput(text=body.text)

    result = score_toxicity(
        input=toxicity_input,
        scorer=scorer,
        trace_id=trace_id,
        span_id=span_id,
    )

    return ScoreResponse(
        toxicity=result.scores.toxicity,
        severe_toxicity=result.scores.severe_toxicity,
        obscene=result.scores.obscene,
        threat=result.scores.threat,
        insult=result.scores.insult,
        identity_hate=result.scores.identity_hate,
        long_response_strategy=result.long_response_strategy,
    )
