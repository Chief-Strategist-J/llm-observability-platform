from __future__ import annotations

from typing import Any
from fastapi import APIRouter, status, Response
from pydantic import BaseModel

from infra.messaging.broker.health_check import KafkaHealthCheck

router = APIRouter()


class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse)
def health() -> Any:
    return HealthResponse(status="ok")


@router.get("/livez")
def liveness_probe() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/readyz")
def readiness_probe(response: Response) -> dict[str, str]:
    kafka_health = KafkaHealthCheck().check_health()
    if not kafka_health.get("healthy", False):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "reason": "kafka_unreachable"}
    return {"status": "ready"}
