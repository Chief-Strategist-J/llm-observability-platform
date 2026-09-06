from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    scorer: str


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> Any:
    gpt2 = request.app.state.gpt2_scorer
    if gpt2.is_available():
        scorer = "gpt2_onnx"
    else:
        scorer = "provider_logprobs"
    return HealthResponse(status="ok", scorer=scorer)
