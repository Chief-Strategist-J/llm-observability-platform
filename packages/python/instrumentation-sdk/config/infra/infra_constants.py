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

    DEFAULT_CHAT_ENDPOINT: str = "/v1/chat/completions"
    DEFAULT_EMBEDDINGS_ENDPOINT: str = "/v1/embeddings"
    DEFAULT_MODEL: str = "gpt-4o"
    DEFAULT_SPAN_NAME_KAFKA_PRODUCE: str = "kafka_produce_span"
    DEFAULT_SPAN_NAME_PROMPT_TOK: str = "prompt_tokenization"
    DEFAULT_SPAN_NAME_MODEL_INFERENCE: str = "model_inference_generation"
    DEFAULT_SPAN_NAME_RESPONSE_FMT: str = "response_formatting"
    DEFAULT_SPAN_NAME_TEXT_CHUNK: str = "text_chunking_and_tokenization"
    DEFAULT_SPAN_NAME_VECTOR_CALC: str = "vector_embedding_calculation"

infra_constants = PlatformInfrastructureConstants()
