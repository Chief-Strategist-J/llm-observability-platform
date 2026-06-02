from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    model_id: str

@router.get("/healthz", response_model=HealthResponse)
def healthz(request: Request) -> Any:
    scorer = request.app.state.toxicity_scorer
    return HealthResponse(status="ok", model_id=scorer.model_id)
