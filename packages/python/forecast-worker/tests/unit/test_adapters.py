import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch
from infra.adapters.redis.redis_adapter import RedisAdapter
from infra.adapters.postgres.postgres_adapter import PostgresAdapter
from infra.adapters.kafka.kafka_alert_adapter import KafkaAlertAdapter

@patch("redis.from_url")
def test_redis_adapter(mock_redis_from_url) -> None:
    mock_client = MagicMock()
    mock_redis_from_url.return_value = mock_client

    adapter = RedisAdapter("redis://localhost:6379/0")
    forecast_time = datetime(2026, 6, 21, 10, 0, 0)

    # Test cache_forecast
    adapter.cache_forecast("service-a", "model-b", forecast_time, 10.0, 8.0, 12.0, 3600)
    mock_client.setex.assert_called_once()
    args, kwargs = mock_client.setex.call_args
    assert args[0] == f"forecast:service-a:model-b:{forecast_time.isoformat()}"
    assert args[1] == 3600
    data = json.loads(args[2])
    assert data["mean"] == 10.0
    assert data["p10"] == 8.0
    assert data["p90"] == 12.0

    # Test get_cached_forecast
    mock_client.get.return_value = json.dumps(data)
    res = adapter.get_cached_forecast("service-a", "model-b", forecast_time)
    assert res == data
    mock_client.get.assert_called_once_with(f"forecast:service-a:model-b:{forecast_time.isoformat()}")

@patch("psycopg.connect")
def test_postgres_adapter(mock_connect) -> None:
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    adapter = PostgresAdapter("postgresql://user:pass@host:5432/db")
    forecast_time = datetime(2026, 6, 21, 10, 0, 0)

    # Test write_forecast
    adapter.write_forecast("service-a", "model-b", forecast_time, 10.0, 8.0, 12.0)
    mock_cur.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

    # Test get_budget_limits
    mock_cur.fetchall.return_value = [("service-a", "model-b", 100.0)]
    mock_cur.execute.reset_mock()
    budgets = adapter.get_budget_limits()
    assert budgets == [("service-a", "model-b", 100.0)]
    mock_cur.execute.assert_called_once()

@patch("infra.adapters.kafka.kafka_alert_adapter.Producer")
def test_kafka_alert_adapter(mock_producer_cls) -> None:
    mock_producer = MagicMock()
    mock_producer_cls.return_value = mock_producer

    adapter = KafkaAlertAdapter("localhost:9092")
    payload = {"service": "service-a", "model": "model-b", "event_type": "predicted_breach"}
    adapter.publish_predicted_breach(payload)

    mock_producer.produce.assert_called_once()
    args, kwargs = mock_producer.produce.call_args
    assert kwargs["topic"] == "alerts.cost.predicted_breach"
    assert kwargs["key"] == b"service-a:model-b"
    data = json.loads(kwargs["value"].decode("utf-8"))
    assert data["event_type"] == "predicted_breach"
    mock_producer.flush.assert_called_once()
