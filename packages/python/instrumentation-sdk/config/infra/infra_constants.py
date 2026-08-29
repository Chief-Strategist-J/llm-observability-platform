from dataclasses import dataclass

@dataclass(frozen=True)
class PlatformInfrastructureConstants:
    TRAEFIK_HTTP_PORT: int = 31410
    TRAEFIK_DASHBOARD_PORT: int = 31411
    TRAEFIK_HTTPS_PORT: int = 31419

    KAFKA_HOST_PORT: int = 31414
    KAFKA_INTERNAL_PORT: int = 9092
    KAFKA_DEFAULT_TOPIC: str = "llm.spans.raw"

    ALLOYDB_HOST_PORT: int = 31420
    ALLOYDB_INTERNAL_PORT: int = 5432

    CLICKHOUSE_HTTP_PORT: int = 8123
    CLICKHOUSE_NATIVE_PORT: int = 9000

    REDIS_HOST_PORT: int = 31413
    REDIS_INTERNAL_PORT: int = 6379

    OTEL_COLLECTOR_HTTP_PORT: int = 31417
    OTEL_COLLECTOR_GRPC_PORT: int = 31418

    TEMPO_HTTP_PORT: int = 31416
    TEMPO_GRPC_HOST_PORT: int = 31423
    TEMPO_GRPC_PORT: int = 4317

    GRAFANA_HOST_PORT: int = 31415

    DEFAULT_INGESTION_HOST: str = "http://localhost:8000"
    DEFAULT_AUTH_SERVICE_HOST: str = "http://localhost:3001"
    DEFAULT_WAL_PATH: str = "/tmp/llm-obs-wal.db"
    DEFAULT_API_KEY_TTL_SEC: int = 60

infra_constants = PlatformInfrastructureConstants()
