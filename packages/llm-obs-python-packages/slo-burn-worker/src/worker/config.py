import os
from dataclasses import dataclass
from shared.errors.base import ValidationError

@dataclass(frozen=True)
class WorkerConfig:
    temporal_host: str
    temporal_namespace: str
    temporal_task_queue: str
    clickhouse_host: str
    clickhouse_port: int
    clickhouse_username: str
    clickhouse_password: str
    clickhouse_database: str
    redis_url: str
    kafka_bootstrap_servers: str
    slo_compliance_config_path: str
    default_slo_compliance: float

def _int_val(raw: str, key: str) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise ValidationError(f"{key} must be an integer") from exc

def _float_val(raw: str, key: str) -> float:
    try:
        return float(raw)
    except ValueError as exc:
        raise ValidationError(f"{key} must be a float") from exc

def load_config(env: dict[str, str] | None = None) -> WorkerConfig:
    source = env or os.environ

    return WorkerConfig(
        temporal_host=source.get("TEMPORAL_HOST", "localhost:7239"),
        temporal_namespace=source.get("TEMPORAL_NAMESPACE", "default"),
        temporal_task_queue=source.get("TEMPORAL_TASK_QUEUE", "slo-burn-tasks"),
        clickhouse_host=source.get("CLICKHOUSE_HOST", "localhost"),
        clickhouse_port=_int_val(
            source.get("CLICKHOUSE_PORT", "8129"), "CLICKHOUSE_PORT"
        ),
        clickhouse_username=source.get("CLICKHOUSE_USERNAME", "default"),
        clickhouse_password=source.get("CLICKHOUSE_PASSWORD", ""),
        clickhouse_database=source.get("CLICKHOUSE_DATABASE", "default"),
        redis_url=source.get("REDIS_URL", "redis://localhost:6389/0"),
        kafka_bootstrap_servers=source.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9099"),
        slo_compliance_config_path=source.get("SLO_COMPLIANCE_CONFIG_PATH", "slo_compliance_config.yaml"),
        default_slo_compliance=_float_val(source.get("DEFAULT_SLO_COMPLIANCE", "0.95"), "DEFAULT_SLO_COMPLIANCE"),
    )
