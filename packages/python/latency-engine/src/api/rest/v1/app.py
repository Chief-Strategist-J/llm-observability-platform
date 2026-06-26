from __future__ import annotations

import logging
import os
import redis
import yaml
from fastapi import FastAPI

from api.rest.v1.router import router as v1_router
from config import load_config
from features.latency_query.service import LatencyQueryService
from infra.adapters.redis.latency_redis_adapter import LatencyRedisAdapter
from infra.adapters.clickhouse.latency_clickhouse_adapter import LatencyClickHouseAdapter
from shared.tracing.tracer import init_tracer

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    init_tracer()
    
    app = FastAPI(
        title="Latency Engine Query API",
        description="Internal service-to-service API for querying latency percentiles, SLO burn rates, and historical baselines.",
        version="1.0.0",
    )

    cfg = load_config()

    # Load SLO thresholds from yaml
    slo_thresholds = {}
    try:
        if os.path.exists(cfg.slo_config_path):
            with open(cfg.slo_config_path, "r") as f:
                slo_config = yaml.safe_load(f) or {}
                slo_thresholds = slo_config.get("endpoints", {})
    except Exception as e:
        logger.error("Failed to load SLO config in app initialization: %s", e)

    # Initialize adapters and services
    redis_client = redis.from_url(cfg.redis_url)
    redis_adapter = LatencyRedisAdapter(redis_client)
    
    clickhouse_adapter = LatencyClickHouseAdapter(
        host=cfg.clickhouse_host,
        port=cfg.clickhouse_port,
        username=cfg.clickhouse_username,
        password=cfg.clickhouse_password,
        database=cfg.clickhouse_database,
    )
    
    query_service = LatencyQueryService(
        redis=redis_adapter,
        clickhouse=clickhouse_adapter,
        slo_thresholds=slo_thresholds,
    )

    # Store in app state
    app.state.query_service = query_service
    
    # Include API endpoints router
    app.include_router(v1_router)
    
    return app

app = create_app()
