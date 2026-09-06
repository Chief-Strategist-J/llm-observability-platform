from typing import Protocol

class MetricsPort(Protocol):
    def record_processed_span(self, service: str, model: str) -> None:
        ...

    def record_fenwick_latency(self, latency_ms: float) -> None:
        ...

    def record_redis_pipeline_latency(self, latency_ms: float) -> None:
        ...

    def record_dlq_event(self, reason: str) -> None:
        ...

    def record_kafka_lag(self, partition: int, lag: int) -> None:
        ...
