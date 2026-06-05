from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    model: str
    device: str

@router.get("/healthz", response_model=HealthResponse)
@router.post("/healthz", response_model=HealthResponse)
def healthz(request: Request) -> Any:
    scorer = request.app.state.nli_scorer
    return HealthResponse(
        status="ok",
        model=scorer.default_model_id,
        device=scorer.device_name,
    )
