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
    LokiManager
)

from .kafka_activity import (
    start_kafka_activity,
    stop_kafka_activity,
    restart_kafka_activity,
    delete_kafka_activity,
    KafkaManager
)

from .grafana_activity import (
    start_grafana_activity,
    stop_grafana_activity,
    restart_grafana_activity,
    delete_grafana_activity,
    GrafanaManager
)

from .jaeger_activity import (
    start_jaeger_activity,
    stop_jaeger_activity,
    restart_jaeger_activity,
    delete_jaeger_activity,
    JaegerManager
)

from .neo4j_activity import (
    start_neo4j_activity,
    stop_neo4j_activity,
    restart_neo4j_activity,
    delete_neo4j_activity,
    Neo4jManager
)

from .opentelemetry_collector import (
    start_opentelemetry_collector,
    stop_opentelemetry_collector,
    restart_opentelemetry_collector,
    delete_opentelemetry_collector,
    OpenTelemetryCollectorManager
)

from .prometheus_activity import (
    start_prometheus_activity,
    stop_prometheus_activity,
    restart_prometheus_activity,
    delete_prometheus_activity,
    PrometheusManager
)

from .promtail_activity import (
    start_promtail_activity,
    stop_promtail_activity,
    restart_promtail_activity,
    delete_promtail_activity,
    PromtailManager
)

from .qdrant_activity import (
    start_qdrant_activity,
    stop_qdrant_activity,
    restart_qdrant_activity,
    delete_qdrant_activity,
    QdrantManager
)

from .redis_activity import (
    start_redis_activity,
    stop_redis_activity,
    restart_redis_activity,
    delete_redis_activity,
    RedisManager
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
    'KafkaManager',
    
    # Activity functions
    'start_loki_activity',
    'stop_loki_activity',
    'restart_loki_activity',
    'delete_loki_activity',
    'start_kafka_activity',
    'stop_kafka_activity',
    'restart_kafka_activity',
    'delete_kafka_activity',
    'start_jaeger_activity',
    'stop_jaeger_activity',
    'restart_jaeger_activity',
    'delete_jaeger_activity',
    'start_neo4j_activity',
    'stop_neo4j_activity',
    'restart_neo4j_activity',
    'delete_neo4j_activity',
    'start_opentelemetry_collector',
    'stop_opentelemetry_collector',
    'restart_opentelemetry_collector',
    'delete_opentelemetry_collector',
    'start_prometheus_activity',
    'stop_prometheus_activity',
    'restart_prometheus_activity',
    'delete_prometheus_activity',
    'start_promtail_activity',
    'stop_promtail_activity',
    'restart_promtail_activity',
    'delete_promtail_activity',
    'start_qdrant_activity',
    'stop_qdrant_activity',
    'restart_qdrant_activity',
    'delete_qdrant_activity',
    'start_redis_activity',
    'stop_redis_activity',
    'restart_redis_activity',
    'delete_redis_activity',
]
