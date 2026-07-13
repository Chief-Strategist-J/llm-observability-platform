from __future__ import annotations
import logging
from prometheus_client import Counter, start_http_server
from shared.ports.metrics_port import MetricsPort

logger = logging.getLogger(__name__)

_server_started = False

SPANS_PROCESSED_TOTAL = Counter(
    "latency_engine_spans_processed_total",
    "Total spans processed by latency-engine",
    ["model", "endpoint", "retry_count"]
)

SKETCH_DROPPED_TOTAL = Counter(
    "latency_sketch_dropped_total",
    "Total sketch updates dropped due to Redis failure",
    ["key"]
)


class PrometheusMetricsAdapter(MetricsPort):
    """
    Adapter implementing MetricsPort using prometheus_client.
    Starts Prometheus HTTP server on port 8000 if not already started.
    """

    def __init__(self) -> None:
        global _server_started
        if not _server_started:
            try:
                start_http_server(8000)
                _server_started = True
                logger.info("Prometheus HTTP server started on port 8000")
            except OSError as e:
                logger.warning("Prometheus HTTP server start failed or already running: %s", e)
                _server_started = True

    def record_span_processed(self, model: str, endpoint: str, retry_count: int) -> None:
        SPANS_PROCESSED_TOTAL.labels(
            model=model,
            endpoint=endpoint,
            retry_count=str(retry_count)
        ).inc()

    def record_sketch_dropped(self, key: str, count: int) -> None:
        SKETCH_DROPPED_TOTAL.labels(key=key).inc(count)
