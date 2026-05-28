from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter()


class ScorerInfo(BaseModel):
    name: str
    model_id: str


class ScorersResponse(BaseModel):
    scorers: list[ScorerInfo]
    primary: str


@router.get("/v1/scorers", response_model=ScorersResponse)
def list_scorers(request: Request) -> Any:
    registry = request.app.state.scorer_registry
    primary = request.app.state.primary_scorer_name
    return ScorersResponse(
        scorers=[
            ScorerInfo(name=m["name"], model_id=m["model_id"])
            for m in registry.models()
        ],
        primary=primary,
    )
