from __future__ import annotations

from typing import Any, Literal
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from shared.tracing.tracer import trace_span

router = APIRouter()


class InferenceRequest(BaseModel):
    text: str
    logprobs: list[list[float]] | None = None


class InferenceResponse(BaseModel):
    perplexity: float | None
    method: Literal["provider_logprobs", "gpt2_onnx"]
    token_count: int


def extract_token_logprobs(logprobs: list[list[float]] | None) -> list[float] | None:
    if logprobs is None:
        return None
    if not logprobs:
        return []
    if len(logprobs) == 1 and len(logprobs[0]) > 1:
        return logprobs[0]
    flat = []
    for item in logprobs:
        if item:
            flat.append(item[0])
    return flat


@router.post("/perplexity", response_model=InferenceResponse)
def compute_perplexity(body: InferenceRequest, request: Request) -> Any:
    logprobs_scorer = request.app.state.logprobs_scorer
    gpt2_scorer = request.app.state.gpt2_scorer

    flat_logprobs = extract_token_logprobs(body.logprobs)

    if flat_logprobs is not None:
        with trace_span("perplexity.inference_provider_logprobs") as span:
            span.set_attribute("provider_logprobs.count", len(flat_logprobs))
            perp = logprobs_scorer.compute(flat_logprobs, body.text)
            span.set_attribute("perplexity.result", perp or 0.0)
            return InferenceResponse(
                perplexity=perp,
                method="provider_logprobs",
                token_count=len(flat_logprobs),
            )

    with trace_span("perplexity.inference_gpt2_fallback") as span:
        if not gpt2_scorer.is_available():
            raise HTTPException(status_code=503, detail="GPT-2 scorer is unavailable")
        perp, token_count = gpt2_scorer.compute_with_token_count(body.text)
        span.set_attribute("gpt2.token_count", token_count)
        span.set_attribute("perplexity.result", perp or 0.0)
        return InferenceResponse(
            perplexity=perp,
            method="gpt2_onnx",
            token_count=token_count,
        )
