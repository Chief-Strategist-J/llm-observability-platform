from __future__ import annotations
import os
from dataclasses import dataclass
from shared.errors.base import ValidationError

@dataclass(frozen=True)
class LatencyEngineConfig:
    kafka_bootstrap_servers: str
    kafka_consumer_group: str
    kafka_topic_input: str
    redis_url: str
    slo_config_path: str
    clickhouse_host: str
    clickhouse_port: int
    clickhouse_username: str
    clickhouse_password: str
    clickhouse_database: str
    temporal_host: str
    temporal_namespace: str
    temporal_task_queue: str
    health_port: int
    jwt_secret: str

def _int_val(raw: str, key: str) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise ValidationError(f"{key} must be an integer") from exc

def load_config(env: dict[str, str] | None = None) -> LatencyEngineConfig:
    source = env or os.environ
    return LatencyEngineConfig(
        kafka_bootstrap_servers = source.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:31414"),
        kafka_consumer_group    = source.get("KAFKA_CONSUMER_GROUP", "latency-engine-cg"),
        kafka_topic_input       = source.get("KAFKA_TOPIC_INPUT", "llm.spans.raw"),
        redis_url               = source.get("REDIS_URL", "redis://:llmobs_redis_s3cret_2024@localhost:31413/0"),
        slo_config_path         = source.get("SLO_CONFIG_PATH", "src/slo_config.yaml"),
        clickhouse_host         = source.get("CLICKHOUSE_HOST", "localhost"),
        clickhouse_port         = _int_val(source.get("CLICKHOUSE_PORT", "31421"), "CLICKHOUSE_PORT"),
        clickhouse_username     = source.get("CLICKHOUSE_USERNAME", "default"),
        clickhouse_password     = source.get("CLICKHOUSE_PASSWORD", "llmobs_clickhouse_s3cret_2026"),
        clickhouse_database     = source.get("CLICKHOUSE_DATABASE", "default"),
        temporal_host           = source.get("TEMPORAL_HOST", "localhost:31424"),
        temporal_namespace      = source.get("TEMPORAL_NAMESPACE", "default"),
        temporal_task_queue     = source.get("TEMPORAL_TASK_QUEUE", "latency-baseline-tasks"),
        health_port             = _int_val(source.get("HEALTH_PORT", "8003"), "HEALTH_PORT"),
        jwt_secret              = source.get("JWT_SECRET", "dev-secret-key-change-in-production"),
    )
