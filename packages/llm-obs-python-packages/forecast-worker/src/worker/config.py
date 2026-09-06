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
    postgres_dsn: str
    kafka_bootstrap_servers: str
    instrumentation_sdk_url: str
    timesfm_repo_id: str
    timesfm_backend: str
    internal_jwt_secret: str

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
    postgres_port = source.get("POSTGRES_PORT", "5432")
    postgres_db = source.get("POSTGRES_DB", "llm_observability")

    postgres_dsn = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    return WorkerConfig(
        temporal_host=source.get("TEMPORAL_HOST", "localhost:7233"),
        temporal_namespace=source.get("TEMPORAL_NAMESPACE", "default"),
        temporal_task_queue=source.get("TEMPORAL_TASK_QUEUE", "forecast-worker-queue"),
        clickhouse_host=source.get("CLICKHOUSE_HOST", "localhost"),
        clickhouse_port=_int_val(
            source.get("CLICKHOUSE_PORT", "8123"), "CLICKHOUSE_PORT"
        ),
        clickhouse_username=source.get("CLICKHOUSE_USER", "default"),
        clickhouse_password=source.get("CLICKHOUSE_PASSWORD", ""),
        clickhouse_database=source.get("CLICKHOUSE_DATABASE", "llm_observability"),
        redis_url=source.get("REDIS_URL", "redis://localhost:6379/0"),
        postgres_dsn=source.get("POSTGRES_DSN", postgres_dsn),
        kafka_bootstrap_servers=source.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        instrumentation_sdk_url=source.get("INSTRUMENTATION_SDK_URL", "http://localhost:8000"),
        timesfm_repo_id=source.get("TIMESFM_REPO_ID", "google/timesfm-1.0-200m"),
        timesfm_backend=source.get("TIMESFM_BACKEND", "cpu"),
        internal_jwt_secret=source.get("INTERNAL_JWT_SECRET", "super-secret-key"),
    )
