import os
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ServiceConfig:
    app_env: str = os.getenv("APP_ENV", "dev")
    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "0.0.0.0")
    
    # Endpoints & URLs
    ingestion_endpoint: str = os.getenv("INGESTION_ENDPOINT", "http://localhost:8000/v1/spans")
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:3001")
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    # Defaults
    default_service_name: str = os.getenv("DEFAULT_SERVICE_NAME", "llm-obs-service")
    wal_db_path: str = os.getenv("WAL_DB_PATH", "/tmp/llm-obs-wal.db")
    api_key_ttl_seconds: int = int(os.getenv("API_KEY_TTL_SECONDS", "60"))

service_config = ServiceConfig()
