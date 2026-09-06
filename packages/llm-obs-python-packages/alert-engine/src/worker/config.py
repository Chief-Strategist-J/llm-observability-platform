import os
from dataclasses import dataclass

class ValidationError(Exception):
    pass

@dataclass(frozen=True)
class WorkerConfig:
    kafka_bootstrap_servers: str
    kafka_consumer_group: str
    kafka_topics: list[str]
    redis_url: str
    postgres_dsn: str
    slack_webhook_url: str
    pagerduty_routing_key: str
    service_owners_file_path: str
    prometheus_metrics_port: int
    health_check_port: int

def _int_val(raw: str, key: str) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise ValidationError(f"{key} must be an integer") from exc

def load_config(env: dict[str, str] | None = None) -> WorkerConfig:
    source = env or os.environ

    postgres_user = source.get("POSTGRES_USER", "postgres")
    postgres_password = source.get("POSTGRES_PASSWORD", "postgres")
    postgres_host = source.get("POSTGRES_HOST", "localhost")
    postgres_port = source.get("POSTGRES_PORT", "5439")
    postgres_db = source.get("POSTGRES_DB", "ewma_db")

    postgres_dsn = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    topics_raw = source.get("KAFKA_TOPICS", "alerts.budget,alerts.cost.anomaly,llm.toxicity.flagged,alerts.quality.degradation,alerts.latency.slo,alerts.latency.ttft_regression")


    kafka_topics = [t.strip() for t in topics_raw.split(",") if t.strip()]

    return WorkerConfig(
        kafka_bootstrap_servers=source.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9099"),
        kafka_consumer_group=source.get("KAFKA_CONSUMER_GROUP", "alert-engine-group"),
        kafka_topics=kafka_topics,
        redis_url=source.get("REDIS_URL", "redis://localhost:6389/0"),
        postgres_dsn=source.get("POSTGRES_DSN", postgres_dsn),
        slack_webhook_url=source.get("SLACK_WEBHOOK_URL", "http://localhost:8080/mock-slack"),
        pagerduty_routing_key=source.get("PAGERDUTY_ROUTING_KEY", "mock-pagerduty-routing-key"),
        service_owners_file_path=source.get("SERVICE_OWNERS_FILE_PATH", "service_owners.yaml"),
        prometheus_metrics_port=_int_val(source.get("PROMETHEUS_METRICS_PORT", "9464"), "PROMETHEUS_METRICS_PORT"),
        health_check_port=_int_val(source.get("HEALTH_CHECK_PORT", "8001"), "HEALTH_CHECK_PORT"),
    )
