import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DatabaseConfig:
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_database: str
    mongo_host: str
    mongo_port: int
    mongo_user: str
    mongo_password: str
    mongo_database: str


@dataclass
class RedisConfig:
    redis_url: str
    ttl_seconds: int


@dataclass
class QueueConfig:
    max_size: int
    per_shard_limit: int


@dataclass
class MetricsConfig:
    window_size: int
    alert_threshold_ms: float


@dataclass
class AppConfig:
    database: DatabaseConfig
    redis: RedisConfig
    queue: QueueConfig
    metrics: MetricsConfig
    benchmark_mode: bool
    test_mode: str


def load_config() -> AppConfig:
    postgres_instances = os.getenv("POSTGRES_INSTANCES", "messaging-postgres:5432").split(",")
    mongo_instances = os.getenv("MONGO_INSTANCES", "messaging-mongodb:27017").split(",")

    database_config = DatabaseConfig(
        postgres_host=postgres_instances[0].split(":")[0] if postgres_instances else "localhost",
        postgres_port=int(postgres_instances[0].split(":")[1]) if postgres_instances and ":" in postgres_instances[0] else 5432,
        postgres_user=os.getenv("POSTGRES_USER", "postgres"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        postgres_database=os.getenv("POSTGRES_DATABASE", "messaging"),
        mongo_host=mongo_instances[0].split(":")[0] if mongo_instances else "localhost",
        mongo_port=int(mongo_instances[0].split(":")[1]) if mongo_instances and ":" in mongo_instances[0] else 27017,
        mongo_user=os.getenv("MONGO_USER", "admin"),
        mongo_password=os.getenv("MONGO_PASSWORD", "admin"),
        mongo_database=os.getenv("MONGO_DATABASE", "kafka_events")
    )

    redis_config = RedisConfig(
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/"),
        ttl_seconds=int(os.getenv("REDIS_TTL_SECONDS", "3600"))
    )

    queue_config = QueueConfig(
        max_size=int(os.getenv("QUEUE_MAX_SIZE", "10000")),
        per_shard_limit=int(os.getenv("QUEUE_PER_SHARD_LIMIT", "10000"))
    )

    metrics_config = MetricsConfig(
        window_size=int(os.getenv("METRICS_WINDOW_SIZE", "1000")),
        alert_threshold_ms=float(os.getenv("METRICS_ALERT_THRESHOLD_MS", "100.0"))
    )

    return AppConfig(
        database=database_config,
        redis=redis_config,
        queue=queue_config,
        metrics=metrics_config,
        benchmark_mode=os.getenv("BENCHMARK_MODE", "false").lower() == "true",
        test_mode=os.getenv("TEST_MODE", "full")
    )
