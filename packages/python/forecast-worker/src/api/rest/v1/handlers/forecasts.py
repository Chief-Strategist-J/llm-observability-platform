import json
import jwt
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# Port interfaces/adapters
from shared.ports.redis_port import RedisPort
from shared.ports.clickhouse_port import ClickHousePort
from shared.ports.postgres_port import PostgresPort
from shared.ports.timesfm_port import TimesFMPort

from features.forecast.service import ForecastService
from features.forecast.repository import ForecastRepository

# HTTP Bearer dependency
security = HTTPBearer(auto_error=False)

def authenticate_jwt(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    token = credentials.credentials
    secret = "super-secret-key"
    if hasattr(request.app.state, "config") and request.app.state.config is not None:
        secret = request.app.state.config.internal_jwt_secret
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        ) from exc

# Dynamic dependency getters to allow seamless local testing and worker running
def get_redis(request: Request) -> RedisPort:
    if not hasattr(request.app.state, "redis") or request.app.state.redis is None:
        from worker.config import load_config
        from infra.adapters.redis.redis_adapter import RedisAdapter
        cfg = load_config()
        request.app.state.redis = RedisAdapter(url=cfg.redis_url)
    return request.app.state.redis

def get_clickhouse(request: Request) -> ClickHousePort:
    if not hasattr(request.app.state, "clickhouse") or request.app.state.clickhouse is None:
        from worker.config import load_config
        from infra.adapters.clickhouse.clickhouse_adapter import ClickHouseAdapter
        cfg = load_config()
        request.app.state.clickhouse = ClickHouseAdapter(
            host=cfg.clickhouse_host,
            port=cfg.clickhouse_port,
            username=cfg.clickhouse_username,
            password=cfg.clickhouse_password,
            database=cfg.clickhouse_database,
        )
    return request.app.state.clickhouse

def get_postgres(request: Request) -> PostgresPort:
    if not hasattr(request.app.state, "postgres") or request.app.state.postgres is None:
        from worker.config import load_config
        from infra.adapters.postgres.postgres_adapter import PostgresAdapter
        cfg = load_config()
        request.app.state.postgres = PostgresAdapter(dsn=cfg.postgres_dsn)
    return request.app.state.postgres

def get_timesfm(request: Request) -> Optional[TimesFMPort]:
    if not hasattr(request.app.state, "timesfm") or request.app.state.timesfm is None:
        try:
            from worker.config import load_config
            from infra.adapters.timesfm.timesfm_adapter import TimesFMAdapter
            cfg = load_config()
            request.app.state.timesfm = TimesFMAdapter(repo_id=cfg.timesfm_repo_id, backend=cfg.timesfm_backend)
        except Exception:
            request.app.state.timesfm = None
    return request.app.state.timesfm


class TriggerRequest(BaseModel):
    lookback_hours: int = Field(default=168, ge=1)
    min_history_hours: int = Field(default=48, ge=1)


async def health() -> dict:
    from api.rest.v1.app import get_health
    try:
        return await get_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def trigger_workflow(request: TriggerRequest | None = None) -> dict:
    from api.rest.v1.app import trigger_forecast_workflow
    try:
        lookback = request.lookback_hours if request else 168
        min_hist = request.min_history_hours if request else 48
        res = await trigger_forecast_workflow(lookback_hours=lookback, min_history_hours=min_hist)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_cost_forecast(
    service: str,
    model: str,
    request: Request,
    user: dict = Depends(authenticate_jwt),
    redis_port: RedisPort = Depends(get_redis),
    clickhouse_port: ClickHousePort = Depends(get_clickhouse),
    postgres_port: PostgresPort = Depends(get_postgres),
    timesfm_port: Optional[TimesFMPort] = Depends(get_timesfm)
) -> dict:
    repo = ForecastRepository(redis_port, clickhouse_port, postgres_port)
    try:
        res, source = ForecastService.get_forecast(service, model, "cost", repo, timesfm_port)
        return {
            "service": service,
            "model": model,
            "mean": res["mean"],
            "p10": res["p10"],
            "p90": res["p90"],
            "forecast_time": res["timestamp"],
            "source": source
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ClickHouse fallback failed: {str(e)}")


async def get_latency_forecast(
    service: str,
    model: str,
    request: Request,
    user: dict = Depends(authenticate_jwt),
    redis_port: RedisPort = Depends(get_redis),
    clickhouse_port: ClickHousePort = Depends(get_clickhouse),
    postgres_port: PostgresPort = Depends(get_postgres),
    timesfm_port: Optional[TimesFMPort] = Depends(get_timesfm)
) -> dict:
    repo = ForecastRepository(redis_port, clickhouse_port, postgres_port)
    try:
        res, source = ForecastService.get_forecast(service, model, "latency", repo, timesfm_port)
        return {
            "service": service,
            "model": model,
            "mean": res["mean"],
            "p10": res["p10"],
            "p90": res["p90"],
            "forecast_time": res["timestamp"],
            "source": source
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ClickHouse fallback failed: {str(e)}")


async def get_cost_breach_risk(
    service: str,
    model: str,
    request: Request,
    user: dict = Depends(authenticate_jwt),
    postgres_port: PostgresPort = Depends(get_postgres),
    redis_port: RedisPort = Depends(get_redis),
    clickhouse_port: ClickHousePort = Depends(get_clickhouse),
    timesfm_port: Optional[TimesFMPort] = Depends(get_timesfm)
) -> dict:
    repo = ForecastRepository(redis_port, clickhouse_port, postgres_port)
    try:
        forecast_res, source = ForecastService.get_forecast(service, model, "cost", repo, timesfm_port)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ClickHouse fallback failed: {str(e)}")

    p90_val = forecast_res["p90"]
    forecast_time = forecast_res["timestamp"]
    
    risk_info = ForecastService.calculate_breach_risk(service, model, p90_val, repo)
    
    return {
        "service": service,
        "model": model,
        "budget_limit": risk_info["budget_limit"],
        "predicted_cost_p90_usd": risk_info["predicted_cost_p90_usd"],
        "breach_predicted": risk_info["breach_predicted"],
        "forecast_time": forecast_time
    }


async def get_forecasts_summary(
    request: Request,
    user: dict = Depends(authenticate_jwt),
    postgres_port: PostgresPort = Depends(get_postgres)
) -> dict:
    repo = ForecastRepository(None, None, postgres_port)
    summary_list = ForecastService.get_forecasts_summary(repo)
    return {
        "forecasts": summary_list
    }
