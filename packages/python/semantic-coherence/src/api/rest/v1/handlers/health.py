from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    scorers: list[str]


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> Any:
    registry = request.app.state.scorer_registry
    return HealthResponse(status="ok", scorers=registry.names())
