import pytest
import psycopg
import redis
from worker.config import load_config
from infra.adapters.postgres.postgres_adapter import PostgresAdapter
from infra.adapters.redis.redis_adapter import RedisAdapter
from shared.types.ewma_types import EwmaRecord


def test_redis_adapter_integration() -> None:
    config = load_config()
    try:
        adapter = RedisAdapter(url=config.redis_url)
        adapter.set_ewma("test-service", "test-model", 99, 12.34)
        val = adapter.get_ewma("test-service", "test-model", 99)
        assert val == 12.34
    except redis.exceptions.ConnectionError:
        pytest.skip("Redis is not available")


def test_postgres_adapter_integration() -> None:
    config = load_config()
    try:
        with psycopg.connect(config.postgres_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except psycopg.OperationalError:
        pytest.skip("PostgreSQL is not available")

    adapter = PostgresAdapter(dsn=config.postgres_dsn)

    with psycopg.connect(config.postgres_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM ewma_baselines WHERE service = 'test-service'")
        conn.commit()

    record = EwmaRecord(
        service="test-service",
        model="test-model",
        hour_of_week=99,
        ewma_value=55.5,
        sample_count=2,
        is_cold_start=True,
    )

    adapter.upsert_baseline(record)
    fetched = adapter.get_baseline("test-service", "test-model", 99)
    assert fetched is not None
    assert fetched.ewma_value == 55.5
    assert fetched.sample_count == 2
    assert fetched.is_cold_start is True
