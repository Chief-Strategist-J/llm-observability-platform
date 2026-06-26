from __future__ import annotations

from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str

@router.get("/health", response_model=HealthResponse)
def health() -> Any:
    return HealthResponse(status="ok")
