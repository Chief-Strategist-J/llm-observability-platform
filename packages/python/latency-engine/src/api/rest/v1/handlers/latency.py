from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from features.latency_query.service import LatencyQueryService
from shared.auth.jwt_verifier import verify_service_jwt, JWTVerificationError
from shared.errors.latency_query_errors import (
    BaselineNotFoundError,
    InvalidQuantileError,
    SketchNotFoundError,
    SLODataNotFoundError,
    AttributionNotFoundError,
)
from shared.tracing.tracer import api_span

logger = logging.getLogger(__name__)

router = APIRouter()


def verify_jwt_token(authorization: str | None = Header(None)) -> None:
    """Enforces HS256 JWT service-to-service authentication."""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "detail": "Missing Authorization header"},
        )
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "detail": "Invalid authorization header format"},
        )
    token = authorization[len("Bearer ") :]
    try:
        verify_service_jwt(token)
    except JWTVerificationError as exc:
        raise HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "detail": str(exc)},
        ) from exc


def get_query_service(request: Request) -> LatencyQueryService:
    """Dependency resolver for LatencyQueryService."""
    return request.app.state.query_service


# Secure all endpoints in this router using the JWT dependency
@router.get(
    "/latency/percentiles",
    dependencies=[Depends(verify_jwt_token)],
    responses={
        400: {"description": "Invalid query parameters"},
        401: {"description": "Missing or invalid JWT"},
        404: {"description": "No sketch found"},
    },
)
def get_percentiles(
    model: str = Query(..., min_length=1),
    hour_of_day: int = Query(..., ge=0, le=23),
    quantiles: str = Query("0.50,0.95,0.99"),
    service: LatencyQueryService = Depends(get_query_service),
) -> Any:
    """DDSketch quantile read from Redis."""
    with api_span(
        "api.get_latency_percentiles",
        {"model": model, "hour_of_day": hour_of_day, "quantiles": quantiles},
    ):
        try:
            q_list = [float(q.strip()) for q in quantiles.split(",")]
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INVALID_PARAM",
                    "detail": "quantiles must be comma-separated floats",
                },
            ) from exc

        try:
            res = service.get_percentiles(model, hour_of_day, q_list)
            return {
                "p50": res.p50,
                "p95": res.p95,
                "p99": res.p99,
                "sample_count": res.sample_count,
            }
        except InvalidQuantileError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_PARAM", "detail": str(exc)},
            ) from exc
        except SketchNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail={"error": "NOT_FOUND", "detail": str(exc)},
            ) from exc


@router.get(
    "/latency/slo",
    dependencies=[Depends(verify_jwt_token)],
    responses={
        400: {"description": "Invalid query parameters"},
        401: {"description": "Missing or invalid JWT"},
        404: {"description": "No SLO data found"},
    },
)
def get_slo(
    model: str = Query(..., min_length=1),
    endpoint: str = Query(..., min_length=1),
    service: LatencyQueryService = Depends(get_query_service),
) -> Any:
    """SLO burn rate read from Redis."""
    with api_span("api.get_latency_slo", {"model": model, "endpoint": endpoint}):
        try:
            res = service.get_slo(model, endpoint)
            return {
                "burn_fast": res.burn_fast,
                "burn_medium": res.burn_medium,
                "burn_slow": res.burn_slow,
                "budget_remaining_pct": res.budget_remaining_pct,
                "slo_threshold_ms": res.slo_threshold_ms,
            }
        except SLODataNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail={"error": "NOT_FOUND", "detail": str(exc)},
            ) from exc


@router.get(
    "/latency/baseline",
    dependencies=[Depends(verify_jwt_token)],
    responses={
        400: {"description": "Invalid query parameters"},
        401: {"description": "Missing or invalid JWT"},
        404: {"description": "No baseline data found"},
    },
)
def get_baseline(
    model: str = Query(..., min_length=1),
    hour_of_day: int = Query(..., ge=0, le=23),
    days: int = Query(7, ge=1, le=90),
    service: LatencyQueryService = Depends(get_query_service),
) -> Any:
    """Historical baseline read from ClickHouse."""
    with api_span(
        "api.get_latency_baseline",
        {"model": model, "hour_of_day": hour_of_day, "days": days},
    ):
        try:
            res_points = service.get_baseline(model, hour_of_day, days)
            return [
                {
                    "date": p.date.isoformat(),
                    "p99_ttft_ms": p.p99_ttft_ms,
                    "p99_total_ms": p.p99_total_ms,
                }
                for p in res_points
            ]
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_PARAM", "detail": str(exc)},
            ) from exc
        except BaselineNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail={"error": "NOT_FOUND", "detail": str(exc)},
            ) from exc


@router.get(
    "/latency/attribution",
    dependencies=[Depends(verify_jwt_token)],
    responses={
        400: {"description": "Invalid query parameters"},
        401: {"description": "Missing or invalid JWT"},
        404: {"description": "No attribution data found"},
    },
)
def get_attribution(
    model: str = Query(..., min_length=1),
    hour: str = Query(..., min_length=10, max_length=10),
    service: LatencyQueryService = Depends(get_query_service),
) -> Any:
    """Average latency attribution segment read from Redis."""
    with api_span("api.get_latency_attribution", {"model": model, "hour": hour}):
        try:
            res = service.get_attribution(model, hour)
            return {
                "dns": res.dns,
                "tcp": res.tcp,
                "queue": res.queue,
                "inference": res.inference,
            }
        except AttributionNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail={"error": "NOT_FOUND", "detail": str(exc)},
            ) from exc

