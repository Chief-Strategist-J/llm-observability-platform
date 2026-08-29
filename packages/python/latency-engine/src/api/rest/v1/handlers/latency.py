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
        404: {"description": "No sketch found"},
    },
)
def get_percentiles(
    model: str = Query(..., min_length=1),
    hour_of_day: int = Query(..., ge=0, le=23),
    quantiles: str = Query("0.50,0.95,0.99"),
    request: Request = None,
    service: LatencyQueryService = Depends(get_query_service),
) -> dict[str, Any]:
    with api_span("get_percentiles", {"model": model, "hour_of_day": hour_of_day}):
        try:
            q_list = [float(q.strip()) for q in quantiles.split(",")]
            for q in q_list:
                if not (0.0 <= q <= 1.0):
                    raise InvalidQuantileError(f"Quantile must be between 0.0 and 1.0, got {q}")
            results = service.get_percentiles(model, hour_of_day, q_list)
            return {"model": model, "hour_of_day": hour_of_day, "quantiles": results}
        except InvalidQuantileError as exc:
            raise HTTPException(status_code=400, detail={"error": "INVALID_QUANTILE", "detail": str(exc)}) from exc
        except SketchNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"error": "SKETCH_NOT_FOUND", "detail": str(exc)}) from exc
        except Exception as exc:
            logger.exception("Unexpected error in get_percentiles")
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "detail": "An internal error occurred"}) from exc

@router.get(
    "/latency/slo",
    dependencies=[Depends(verify_jwt_token)],
    responses={
        400: {"description": "Invalid query parameters"},
        401: {"description": "Missing or invalid JWT"},
        404: {"description": "No SLO data found"},
    },
)
def get_slo_compliance(
    model: str = Query(..., min_length=1),
    endpoint: str = Query(..., min_length=1),
    time_window: str = Query("1h"),
    request: Request = None,
    service: LatencyQueryService = Depends(get_query_service),
) -> dict[str, Any]:
    with api_span("get_slo_compliance", {"model": model, "endpoint": endpoint}):
        try:
            compliance = service.get_slo_compliance(model, endpoint, time_window)
            return {
                "model": model,
                "endpoint": endpoint,
                "slo_target_ms": compliance.target_ms,
                "compliance_pct": compliance.compliance_pct,
                "total_requests": compliance.total_requests,
                "violations": compliance.violations,
            }
        except SLODataNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"error": "SLO_DATA_NOT_FOUND", "detail": str(exc)}) from exc
        except Exception as exc:
            logger.exception("Unexpected error in get_slo_compliance")
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "detail": "An internal error occurred"}) from exc

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
    request: Request = None,
    service: LatencyQueryService = Depends(get_query_service),
) -> dict[str, Any]:
    with api_span("get_attribution", {"model": model, "hour": hour}):
        try:
            breakdown = service.get_attribution_breakdown(model, hour)
            return {
                "model": model,
                "hour": hour,
                "breakdown": breakdown,
            }
        except AttributionNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"error": "ATTRIBUTION_NOT_FOUND", "detail": str(exc)}) from exc
        except Exception as exc:
            logger.exception("Unexpected error in get_attribution")
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "detail": "An internal error occurred"}) from exc

@router.get(
    "/latency/baseline",
    dependencies=[Depends(verify_jwt_token)],
    responses={
        400: {"description": "Invalid query parameters"},
        401: {"description": "Missing or invalid JWT"},
        404: {"description": "No baseline found"},
    },
)
def get_baseline(
    model: str = Query(..., min_length=1),
    hour_of_day: int = Query(..., ge=0, le=23),
    days: int = Query(7, ge=1, le=30),
    request: Request = None,
    service: LatencyQueryService = Depends(get_query_service),
) -> dict[str, Any]:
    with api_span("get_baseline", {"model": model, "hour_of_day": hour_of_day}):
        try:
            baseline = service.get_baseline(model, hour_of_day, days)
            return {
                "model": model,
                "hour_of_day": hour_of_day,
                "lookback_days": days,
                "baseline_p99_ms": baseline.p99_ms,
                "samples_count": baseline.samples_count,
            }
        except BaselineNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"error": "BASELINE_NOT_FOUND", "detail": str(exc)}) from exc
        except Exception as exc:
            logger.exception("Unexpected error in get_baseline")
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "detail": "An internal error occurred"}) from exc
