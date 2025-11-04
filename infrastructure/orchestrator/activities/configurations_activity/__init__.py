"""
Configuration activities for the orchestrator.

This package contains activity implementations for managing various infrastructure components
like monitoring, logging, and storage services.
"""

# Manager classes
from .grafana_activity import GrafanaManager
from .jaeger_activity import JaegerManager
from .neo4j_activity import Neo4jManager
from .opentelemetry_collector import OpenTelemetryCollectorManager
from .prometheus_activity import PrometheusManager
from .promtail_activity import PromtailManager
from .qdrant_activity import QdrantManager
from .redis_activity import RedisManager

# Activity functions - import functions directly to avoid circular imports
from .loki_activity import (
    start_loki_activity,
    stop_loki_activity,
    restart_loki_activity,
    delete_loki_activity,
)

# Lazy import LokiManager to avoid circular imports
LokiManager = None
def _import_loki_manager():
    global LokiManager
    if LokiManager is None:
        from .loki_activity import LokiManager as _LokiManager
        LokiManager = _LokiManager

__all__ = [
    # Manager classes
    'GrafanaManager',
    'JaegerManager',
    'LokiManager',
    'Neo4jManager',
    'OpenTelemetryCollectorManager',
    'PrometheusManager',
    'PromtailManager',
    'QdrantManager',
    'RedisManager',
    
    # Activity functions
    'start_loki_activity',
    'stop_loki_activity',
    'restart_loki_activity',
    'delete_loki_activity',
]
