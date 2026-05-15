from dataclasses import dataclass
import os

from shared.errors.base import ValidationError

DEFAULT_EMBEDDING_DIMENSIONS = 1536
DEFAULT_CONCURRENCY = 5
DEFAULT_RATE_LIMIT_PER_SEC = 50
DEFAULT_BACKOFF_MS = 500
DEFAULT_EMBEDDING_PROVIDER = "cloudflare"


@dataclass(frozen=True)
class WorkerConfig:
    account_id: str
    queue_name: str
    embedding_dimensions: int
    concurrency: int
    rate_limit_per_sec: int
    backoff_ms: int
    embedding_provider: str


def _positive_int(raw: str, key: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValidationError(f"{key} must be an integer") from exc
    if value <= 0:
        raise ValidationError(f"{key} must be greater than zero")
    return value


def load_config(env: dict[str, str] | None = None) -> WorkerConfig:
    source = env or os.environ
    return WorkerConfig(
        account_id=source.get("CF_ACCOUNT_ID", "local-account"),
        queue_name=source.get("CF_QUEUE_NAME", "span-enrichment"),
        embedding_dimensions=_positive_int(source.get("EMBEDDING_DIMENSIONS", str(DEFAULT_EMBEDDING_DIMENSIONS)), "EMBEDDING_DIMENSIONS"),
        concurrency=_positive_int(source.get("WORKER_CONCURRENCY", str(DEFAULT_CONCURRENCY)), "WORKER_CONCURRENCY"),
        rate_limit_per_sec=_positive_int(source.get("WORKER_RATE_LIMIT_PER_SEC", str(DEFAULT_RATE_LIMIT_PER_SEC)), "WORKER_RATE_LIMIT_PER_SEC"),
        backoff_ms=_positive_int(source.get("WORKER_BACKOFF_MS", str(DEFAULT_BACKOFF_MS)), "WORKER_BACKOFF_MS"),
        embedding_provider=source.get("EMBEDDING_PROVIDER", DEFAULT_EMBEDDING_PROVIDER),
    )
