import os
from dataclasses import dataclass
from .infra_constants import infra_constants

@dataclass(frozen=True)
class ServiceConfig:
    app_env: str = os.getenv("APP_ENV", "dev")
    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "0.0.0.0")
    
    ingestion_endpoint: str = os.getenv("INGESTION_ENDPOINT", f"{infra_constants.DEFAULT_INGESTION_HOST}/v1/spans")
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", infra_constants.DEFAULT_AUTH_SERVICE_HOST)
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", f"localhost:{infra_constants.KAFKA_HOST_PORT}")
    kafka_default_topic: str = os.getenv("KAFKA_DEFAULT_TOPIC", infra_constants.KAFKA_DEFAULT_TOPIC)
    
    otel_exporter_endpoint: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", f"localhost:{infra_constants.TEMPO_GRPC_HOST_PORT}")
    skip_otlp_exporter: str = os.getenv("SKIP_OTLP_EXPORTER", "false")
    skip_console_exporter: str = os.getenv("SKIP_CONSOLE_EXPORTER", "true")

    default_service_name: str = os.getenv("DEFAULT_SERVICE_NAME", "llm-observability-platform")
    service_version: str = os.getenv("SERVICE_VERSION", "0.1.0")
    wal_db_path: str = os.getenv("WAL_DB_PATH", infra_constants.DEFAULT_WAL_PATH)
    api_key_ttl_seconds: int = int(os.getenv("API_KEY_TTL_SECONDS", str(infra_constants.DEFAULT_API_KEY_TTL_SEC)))

    chat_endpoint: str = infra_constants.DEFAULT_CHAT_ENDPOINT
    embeddings_endpoint: str = infra_constants.DEFAULT_EMBEDDINGS_ENDPOINT
    default_model: str = infra_constants.DEFAULT_MODEL

    span_name_kafka_produce: str = infra_constants.DEFAULT_SPAN_NAME_KAFKA_PRODUCE
    span_name_prompt_tok: str = infra_constants.DEFAULT_SPAN_NAME_PROMPT_TOK
    span_name_model_inference: str = infra_constants.DEFAULT_SPAN_NAME_MODEL_INFERENCE
    span_name_response_fmt: str = infra_constants.DEFAULT_SPAN_NAME_RESPONSE_FMT
    span_name_text_chunk: str = infra_constants.DEFAULT_SPAN_NAME_TEXT_CHUNK
    span_name_vector_calc: str = infra_constants.DEFAULT_SPAN_NAME_VECTOR_CALC

service_config = ServiceConfig()
