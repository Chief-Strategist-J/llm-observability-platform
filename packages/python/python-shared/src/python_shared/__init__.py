"""
python-shared: Centralized infrastructure, telemetry, db, http, kafka, discovery, and shared types.
Modeled after packages/node/shared-infra.
"""

from python_shared.types import BaseResponse, HealthStatusResponse
from python_shared.telemetry import setup_telemetry, get_tracer, REQUEST_COUNT, REQUEST_LATENCY
from python_shared.http import ResilientHttpClient, CircuitBreaker, CorrelationAndTelemetryMiddleware
from python_shared.db import get_redis_client, get_redis_pool, get_postgres_connection
from python_shared.kafka import get_kafka_producer, get_kafka_consumer
from python_shared.discovery import resolve_service_endpoint
from python_shared.feature_flags import evaluate_flag

__all__ = [
    "BaseResponse",
    "HealthStatusResponse",
    "setup_telemetry",
    "get_tracer",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "ResilientHttpClient",
    "CircuitBreaker",
    "CorrelationAndTelemetryMiddleware",
    "get_redis_client",
    "get_redis_pool",
    "get_postgres_connection",
    "get_kafka_producer",
    "get_kafka_consumer",
    "resolve_service_endpoint",
    "evaluate_flag",
]
