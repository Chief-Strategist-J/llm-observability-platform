from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    model_id: str


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> Any:
    nli_scorer = request.app.state.nli_scorer
    return HealthResponse(status="ok", model_id=nli_scorer.model_id)
