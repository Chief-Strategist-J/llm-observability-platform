import os
from dataclasses import dataclass

class ValidationError(Exception):
    pass

@dataclass(frozen=True)
class Config:
    redis_url: str
    postgres_dsn: str
    internal_jwt_secret: str
    host: str
    port: int

def _int_val(raw: str, key: str) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise ValidationError(f"{key} must be an integer") from exc

def load_config(env: dict[str, str] | None = None) -> Config:
    source = env or os.environ
    postgres_user = source.get("POSTGRES_USER", "postgres")
    postgres_password = source.get("POSTGRES_PASSWORD", "postgres")
    postgres_host = source.get("POSTGRES_HOST", "localhost")
    postgres_port = source.get("POSTGRES_PORT", "5439")
    postgres_db = source.get("POSTGRES_DB", "ewma_db")
    postgres_dsn = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    
    return Config(
        redis_url=source.get("REDIS_URL", "redis://localhost:6389/0"),
        postgres_dsn=source.get("POSTGRES_DSN", postgres_dsn),
        internal_jwt_secret=source.get("INTERNAL_JWT_SECRET", "super-secret-key"),
        host=source.get("HOST", "0.0.0.0"),
        port=_int_val(source.get("PORT", "8001"), "PORT"),
    )
