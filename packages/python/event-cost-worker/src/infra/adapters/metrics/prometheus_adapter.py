from prometheus_client import Counter, Histogram, Gauge
from shared.ports.metrics_port import MetricsPort

SPANS_PROCESSED = Counter(
    "cost_engine_spans_processed_total",
    "Total spans processed by cost engine",
    ["service", "model"]
)

FENWICK_LATENCY = Histogram(
    "cost_engine_fenwick_update_latency_ms",
    "Latency of Fenwick Tree updates in milliseconds"
)

REDIS_PIPELINE_LATENCY = Histogram(
    "cost_engine_redis_pipeline_latency_ms",
    "Latency of Redis pipeline execution in milliseconds"
)

DLQ_TOTAL = Counter(
    "cost_engine_dlq_total",
    "Total spans sent to DLQ",
    ["reason"]
)

KAFKA_LAG = Gauge(
    "cost_engine_kafka_lag",
    "Kafka consumer lag per partition",
    ["partition"]
)

class PrometheusAdapter(MetricsPort):
    def record_processed_span(self, service: str, model: str) -> None:
        SPANS_PROCESSED.labels(service=service, model=model).inc()

    def record_fenwick_latency(self, latency_ms: float) -> None:
        FENWICK_LATENCY.observe(latency_ms)

    def record_redis_pipeline_latency(self, latency_ms: float) -> None:
        REDIS_PIPELINE_LATENCY.observe(latency_ms)

    def record_dlq_event(self, reason: str) -> None:
        DLQ_TOTAL.labels(reason=reason).inc()

    def record_kafka_lag(self, partition: int, lag: int) -> None:
        KAFKA_LAG.labels(partition=partition).set(lag)
