from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from core.domain.service import score_nli
from core.domain.types import NliInput

router = APIRouter()

class NliRequest(BaseModel):
    context: str
    sentences: list[str]
    temperature: float = Field(default=1.5, ge=0.0)

class SentenceProbabilitySchema(BaseModel):
    entailment: float
    neutral: float
    contradiction: float

class SentenceResultSchema(BaseModel):
    sentence: str
    label: str
    probabilities: SentenceProbabilitySchema

class NliResponse(BaseModel):
    results: list[SentenceResultSchema]
    faithfulness_score: float
    flagged_sentences: list[str]

@router.post("/nli", response_model=NliResponse)
def score_endpoint(body: NliRequest, request: Request) -> Any:
    scorer = request.app.state.nli_scorer

    traceparent = request.headers.get("traceparent")
    trace_id = None
    span_id = None
    if traceparent:
        parts = traceparent.split("-")
        if len(parts) >= 3:
            trace_id = parts[1]
            span_id = parts[2]

    # Validate temperature to prevent division by zero in model
    temp = body.temperature if body.temperature > 0 else 1.5

    nli_input = NliInput(
        context=body.context,
        sentences=body.sentences,
        temperature=temp,
    )

    result = score_nli(
        input=nli_input,
        scorer=scorer,
        trace_id=trace_id,
        span_id=span_id,
    )

    return NliResponse(
        results=[
            SentenceResultSchema(
                sentence=r.sentence,
                label=r.label,
                probabilities=SentenceProbabilitySchema(
                    entailment=r.probabilities.entailment,
                    neutral=r.probabilities.neutral,
                    contradiction=r.probabilities.contradiction,
                ),
            )
            for r in result.results
        ],
        faithfulness_score=result.faithfulness_score,
        flagged_sentences=result.flagged_sentences,
    )
