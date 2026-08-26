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
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", f"localhost:{infra_constants.KAFKA_INTERNAL_PORT}")
    
    default_service_name: str = os.getenv("DEFAULT_SERVICE_NAME", "llm-obs-service")
    wal_db_path: str = os.getenv("WAL_DB_PATH", infra_constants.DEFAULT_WAL_PATH)
    api_key_ttl_seconds: int = int(os.getenv("API_KEY_TTL_SECONDS", str(infra_constants.DEFAULT_API_KEY_TTL_SEC)))

service_config = ServiceConfig()
