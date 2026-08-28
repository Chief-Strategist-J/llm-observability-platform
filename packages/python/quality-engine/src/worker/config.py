from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class QualityEngineConfig:
    # Kafka consumer
    kafka_bootstrap_servers: str
    kafka_consumer_group: str
    kafka_topic_input: str
    kafka_topic_scores: str
    kafka_topic_toxicity: str
    kafka_topic_alerts: str

    # PostgreSQL (shared)
    postgres_dsn: str

    # Redis (shared)
    redis_url: str

    # Temporal — event trigger (quality_score_workflow)
    temporal_host: str
    temporal_namespace: str
    temporal_task_queue: str

    # Temporal — baseline scheduler (separate task queue)
    temporal_baseline_task_queue: str

    # ClickHouse (quality_trend rollup)
    clickhouse_host: str
    clickhouse_port: int
    clickhouse_username: str
    clickhouse_password: str
    clickhouse_database: str

    # Embedding worker
    embedding_worker_url: str

    # Consumer concurrency
    consumer_concurrency: int


def load_config(env: dict[str, str] | None = None) -> QualityEngineConfig:
    source = env or os.environ

    pg_user = source.get("POSTGRES_USER", "postgres")
    pg_pass = source.get("POSTGRES_PASSWORD", "postgres")
    pg_host = source.get("POSTGRES_HOST", "localhost")
    pg_port = source.get("POSTGRES_PORT", "5432")
    pg_db   = source.get("POSTGRES_DB", "quality_engine_db")
    pg_dsn  = source.get(
        "POSTGRES_DSN",
        f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    )

    return QualityEngineConfig(
        kafka_bootstrap_servers = source.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        kafka_consumer_group    = source.get("KAFKA_CONSUMER_GROUP", "quality-engine-group"),
        kafka_topic_input       = source.get("KAFKA_TOPIC_INPUT", "llm.spans.sampled"),
        kafka_topic_scores      = source.get("KAFKA_TOPIC_SCORES", "llm.quality.scores"),
        kafka_topic_toxicity    = source.get("KAFKA_TOPIC_TOXICITY", "llm.toxicity.flagged"),
        kafka_topic_alerts      = source.get("KAFKA_TOPIC_ALERTS", "alerts.quality.degradation"),
        postgres_dsn            = pg_dsn,
        redis_url               = source.get("REDIS_URL", "redis://localhost:6379/0"),
        temporal_host           = source.get("TEMPORAL_HOST", "localhost:7233"),
        temporal_namespace      = source.get("TEMPORAL_NAMESPACE", "default"),
        temporal_task_queue     = source.get("TEMPORAL_TASK_QUEUE", "quality-engine-tasks"),
        temporal_baseline_task_queue = source.get("TEMPORAL_BASELINE_TASK_QUEUE", "quality-baseline-tasks"),
        clickhouse_host         = source.get("CLICKHOUSE_HOST", "localhost"),
        clickhouse_port         = int(source.get("CLICKHOUSE_PORT", "8123")),
        clickhouse_username     = source.get("CLICKHOUSE_USERNAME", "default"),
        clickhouse_password     = source.get("CLICKHOUSE_PASSWORD", ""),
        clickhouse_database     = source.get("CLICKHOUSE_DATABASE", "default"),
        embedding_worker_url    = source.get("EMBEDDING_WORKER_URL", "http://localhost:8001"),
        consumer_concurrency    = int(source.get("CONSUMER_CONCURRENCY", "4")),
    )
