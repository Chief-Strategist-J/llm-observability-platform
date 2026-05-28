import os
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkerConfig:
    kafka_bootstrap_servers: str
    kafka_consumer_group: str
    kafka_topic: str
    kafka_dlq_topic: str
    redis_url: str
    poll_timeout_s: float = 1.0
    batch_size: int = 500
    max_retries: int = 3
    retry_base_ms: int = 100
    price_config_path: str = "model_price_versions.yaml"
    prometheus_metrics_port: int = 9465


def load_config(env: dict[str, str] | None = None) -> WorkerConfig:
    source = env or os.environ

    return WorkerConfig(
        kafka_bootstrap_servers=source.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        kafka_consumer_group=source.get("KAFKA_CONSUMER_GROUP", "event-cost-worker-group"),
        kafka_topic=source.get("KAFKA_TOPIC", "llm.spans.raw"),
        kafka_dlq_topic=source.get("KAFKA_DLQ_TOPIC", "llm.spans.raw.dlq"),
        redis_url=source.get("REDIS_URL", "redis://localhost:6379/0"),
        poll_timeout_s=float(source.get("POLL_TIMEOUT_S", "1.0")),
        batch_size=int(source.get("BATCH_SIZE", "500")),
        max_retries=int(source.get("MAX_RETRIES", "3")),
        retry_base_ms=int(source.get("RETRY_BASE_MS", "100")),
        price_config_path=source.get("PRICE_CONFIG_PATH", "model_price_versions.yaml"),
        prometheus_metrics_port=int(source.get("PROMETHEUS_METRICS_PORT", "9465")),
    )
