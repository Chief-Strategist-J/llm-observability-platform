from fastapi import APIRouter, Depends, Request
from typing import Optional
from api.rest.v1.handlers import forecasts as handlers

router = APIRouter()

@router.get("/health")
async def health():
    return await handlers.health()

@router.post("/trigger")
async def trigger_workflow(request: handlers.TriggerRequest | None = None):
    return await handlers.trigger_workflow(request)

@router.get("/forecasts/cost/{service}/{model}")
async def get_cost_forecast(
    service: str,
    model: str,
    request: Request,
    user: dict = Depends(handlers.authenticate_jwt),
    redis_port = Depends(handlers.get_redis),
    clickhouse_port = Depends(handlers.get_clickhouse),
    postgres_port = Depends(handlers.get_postgres),
    timesfm_port = Depends(handlers.get_timesfm)
):
    return await handlers.get_cost_forecast(
        service=service,
        model=model,
        request=request,
        user=user,
        redis_port=redis_port,
        clickhouse_port=clickhouse_port,
        postgres_port=postgres_port,
        timesfm_port=timesfm_port
    )

@router.get("/forecasts/latency/{service}/{model}")
async def get_latency_forecast(
    service: str,
    model: str,
    request: Request,
    user: dict = Depends(handlers.authenticate_jwt),
    redis_port = Depends(handlers.get_redis),
    clickhouse_port = Depends(handlers.get_clickhouse),
    postgres_port = Depends(handlers.get_postgres),
    timesfm_port = Depends(handlers.get_timesfm)
):
    return await handlers.get_latency_forecast(
        service=service,
        model=model,
        request=request,
        user=user,
        redis_port=redis_port,
        clickhouse_port=clickhouse_port,
        postgres_port=postgres_port,
        timesfm_port=timesfm_port
    )

@router.get("/forecasts/cost/{service}/{model}/breach-risk")
async def get_cost_breach_risk(
    service: str,
    model: str,
    request: Request,
    user: dict = Depends(handlers.authenticate_jwt),
    postgres_port = Depends(handlers.get_postgres),
    redis_port = Depends(handlers.get_redis),
    clickhouse_port = Depends(handlers.get_clickhouse),
    timesfm_port = Depends(handlers.get_timesfm)
):
    return await handlers.get_cost_breach_risk(
        service=service,
        model=model,
        request=request,
        user=user,
        postgres_port=postgres_port,
        redis_port=redis_port,
        clickhouse_port=clickhouse_port,
        timesfm_port=timesfm_port
    )

@router.get("/forecasts/summary")
async def get_forecasts_summary(
    request: Request,
    user: dict = Depends(handlers.authenticate_jwt),
    postgres_port = Depends(handlers.get_postgres)
):
    return await handlers.get_forecasts_summary(
        request=request,
        user=user,
        postgres_port=postgres_port
    )
