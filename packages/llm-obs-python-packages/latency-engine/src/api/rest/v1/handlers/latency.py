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

logger = logging.getLogger(__name__)

router = APIRouter()

def verify_jwt_token(authorization: str | None = Header(None)) -> None:
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
    return request.app.state.query_service

@router.get(
    "/latency/percentiles",
    dependencies=[Depends(verify_jwt_token)],
    responses={
        400: {"description": "Invalid query parameters"},
        401: {"description": "Missing or invalid JWT"},
    },
)
def get_percentiles(
    model: str = Query(..., min_length=1),
    hour_of_day: int = Query(..., ge=0, le=23),
    quantiles: str = Query("0.50,0.95,0.99"),
    service: LatencyQueryService = Depends(get_query_service),
) -> dict[str, Any]:
    try:
        q_list = [float(q.strip()) for q in quantiles.split(",")]
        for q in q_list:
            if not (0.0 <= q <= 1.0):
                raise InvalidQuantileError(f"Quantile must be between 0.0 and 1.0, got {q}")
        results = service.get_percentiles(model, hour_of_day, q_list)
        return {
            "p50": results.p50,
            "p95": results.p95,
            "p99": results.p99,
            "sample_count": results.sample_count,
        }
    except SketchNotFoundError:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "sample_count": 0}
    except InvalidQuantileError as exc:
        raise HTTPException(status_code=400, detail={"error": "INVALID_QUANTILE", "detail": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Unexpected error in get_percentiles")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "detail": "An internal error occurred"}) from exc

@router.get(
    "/latency/slo",
    dependencies=[Depends(verify_jwt_token)],
    responses={
        400: {"description": "Invalid query parameters"},
        401: {"description": "Missing or invalid JWT"},
    },
)
def get_slo_compliance(
    model: str = Query(..., min_length=1),
    endpoint: str = Query(..., min_length=1),
    time_window: str = Query("1h"),
    service: LatencyQueryService = Depends(get_query_service),
) -> dict[str, Any]:
    try:
        compliance = service.get_slo(model, endpoint)
        return {
            "burn_fast": compliance.burn_fast,
            "burn_medium": compliance.burn_medium,
            "burn_slow": compliance.burn_slow,
            "budget_remaining_pct": compliance.budget_remaining_pct,
            "slo_threshold_ms": compliance.slo_threshold_ms,
        }
    except SLODataNotFoundError:
        return {
            "burn_fast": 0.0,
            "burn_medium": 0.0,
            "burn_slow": 0.0,
            "budget_remaining_pct": 100.0,
            "slo_threshold_ms": 1000.0,
        }
    except Exception as exc:
        logger.exception("Unexpected error in get_slo_compliance")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "detail": "An internal error occurred"}) from exc

@router.get(
    "/latency/attribution",
    dependencies=[Depends(verify_jwt_token)],
    responses={
        400: {"description": "Invalid query parameters"},
        401: {"description": "Missing or invalid JWT"},
    },
)
def get_attribution(
    model: str = Query(..., min_length=1),
    hour: str = Query(..., min_length=10, max_length=10),
    service: LatencyQueryService = Depends(get_query_service),
) -> dict[str, Any]:
    try:
        attr = service.get_attribution(model, hour)
        return {
            "dns": attr.dns,
            "tcp": attr.tcp,
            "queue": attr.queue,
            "inference": attr.inference,
        }
    except AttributionNotFoundError:
        return {
            "dns": 0.0,
            "tcp": 0.0,
            "queue": 0.0,
            "inference": 0.0,
        }
    except Exception as exc:
        logger.exception("Unexpected error in get_attribution")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "detail": "An internal error occurred"}) from exc

@router.get(
    "/latency/baseline",
    dependencies=[Depends(verify_jwt_token)],
    responses={
        400: {"description": "Invalid query parameters"},
        401: {"description": "Missing or invalid JWT"},
    },
)
def get_baseline(
    model: str = Query(..., min_length=1),
    hour_of_day: int = Query(..., ge=0, le=23),
    days: int = Query(7, ge=1, le=30),
    service: LatencyQueryService = Depends(get_query_service),
) -> list[dict[str, Any]]:
    try:
        baseline_points = service.get_baseline(model, hour_of_day, days)
        return [
            {
                "date": str(b.date),
                "p99_ttft_ms": b.p99_ttft_ms,
                "p99_total_ms": b.p99_total_ms,
            }
            for b in baseline_points
        ]
    except BaselineNotFoundError:
        return []
    except Exception as exc:
        logger.exception("Unexpected error in get_baseline")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "detail": "An internal error occurred"}) from exc
