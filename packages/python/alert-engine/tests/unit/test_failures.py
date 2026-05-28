import json
import logging
from typing import Any
import pytest
from unittest.mock import MagicMock, patch

from handlers.alerts_budget.handler import BudgetAlertHandler
from handlers.alerts_cost_anomaly.handler import CostAnomalyAlertHandler
from worker.index import main

class DummyException(Exception):
    pass

class MockDbPort:
    def __init__(self, raise_exc: bool = False) -> None:
        self.raise_exc = raise_exc
        self.calls: list[dict] = []

    def insert_alert(self, *args, **kwargs) -> None:
        if self.raise_exc:
            raise DummyException("Database insertion failed")
        self.calls.append({"args": args, "kwargs": kwargs})

class MockRedisPort:
    def __init__(self, allowed: bool = True, raise_exc: bool = False) -> None:
        self.allowed = allowed
        self.raise_exc = raise_exc
        self.calls: list[dict] = []

    def acquire_rate_limit(self, key: str, ttl_seconds: int) -> bool:
        if self.raise_exc:
            raise DummyException("Redis connection lost")
        self.calls.append({"key": key, "ttl": ttl_seconds})
        return self.allowed

class MockSlackPort:
    def __init__(self, raise_exc: bool = False) -> None:
        self.raise_exc = raise_exc
        self.channel_calls: list[dict] = []

    def send_channel_message(self, channel: str, text: str) -> None:
        if self.raise_exc:
            raise DummyException("Slack API timeout")
        self.channel_calls.append({"channel": channel, "text": text})

    def send_direct_message(self, user: str, text: str) -> None:
        if self.raise_exc:
            raise DummyException("Slack API timeout")

class MockPagerDutyPort:
    def __init__(self, raise_exc: bool = False) -> None:
        self.raise_exc = raise_exc
        self.calls: list[dict] = []

    def trigger_incident(self, *args, **kwargs) -> None:
        if self.raise_exc:
            raise DummyException("PagerDuty API failed")
        self.calls.append({"args": args, "kwargs": kwargs})

class MockMetricsPort:
    def record_delivery_latency(self, *args, **kwargs) -> None:
        pass

def test_handler_database_failure() -> None:
    db = MockDbPort(raise_exc=True)
    redis = MockRedisPort()
    slack = MockSlackPort()
    metrics = MockMetricsPort()

    handler = BudgetAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        metrics_port=metrics,
        service_owners_path="service_owners.yaml"
    )

    payload = {
        "user_id": "usr-123",
        "model": "gpt-4",
        "event_type": "blocked"
    }

    with pytest.raises(DummyException):
        handler.handle(payload)

def test_handler_redis_failure() -> None:
    db = MockDbPort()
    redis = MockRedisPort(raise_exc=True)
    slack = MockSlackPort()
    metrics = MockMetricsPort()

    handler = BudgetAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        metrics_port=metrics,
        service_owners_path="service_owners.yaml"
    )

    payload = {
        "user_id": "usr-123",
        "model": "gpt-4",
        "event_type": "blocked"
    }

    with pytest.raises(DummyException):
        handler.handle(payload)

def test_handler_slack_failure() -> None:
    db = MockDbPort()
    redis = MockRedisPort()
    slack = MockSlackPort(raise_exc=True)
    metrics = MockMetricsPort()

    handler = BudgetAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        metrics_port=metrics,
        service_owners_path="service_owners.yaml"
    )

    payload = {
        "user_id": "usr-123",
        "model": "gpt-4",
        "event_type": "blocked"
    }

    with pytest.raises(DummyException):
        handler.handle(payload)

def test_handler_pagerduty_failure() -> None:
    db = MockDbPort()
    redis = MockRedisPort()
    slack = MockSlackPort()
    pd = MockPagerDutyPort(raise_exc=True)
    metrics = MockMetricsPort()

    handler = CostAnomalyAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        pagerduty_port=pd,
        metrics_port=metrics
    )

    payload = {
        "service": "billing_service",
        "model": "gpt-4",
        "sample_count": 10,
        "current_cost": 12.0,
        "ewma_value": 2.0,
        "threshold_value": 6.0
    }

    with pytest.raises(DummyException):
        handler.handle(payload)

class MockKafkaMessage:
    def __init__(self, topic: str, value: bytes, error_code: int = 0) -> None:
        self._topic = topic
        self._value = value
        self._error_code = error_code

    def topic(self) -> str:
        return self._topic

    def value(self) -> bytes:
        return self._value

    def error(self) -> Any:
        if self._error_code != 0:
            mock_err = MagicMock()
            mock_err.code.return_value = self._error_code
            return mock_err
        return None

    def headers(self) -> list[tuple[str, bytes]] | None:
        return None

def test_consumer_loop_resilience() -> None:
    messages = [
        MockKafkaMessage("alerts.budget", b"invalid-json-content"),
        MockKafkaMessage("alerts.budget", json.dumps({
            "user_id": "usr-999",
            "model": "gpt-4",
            "event_type": "blocked"
        }).encode("utf-8")),
        None
    ]
    iterator = iter(messages)

    mock_consumer_instance = MagicMock()
    mock_consumer_instance.poll.side_effect = lambda timeout: next(iterator)

    with patch("worker.index.Consumer", return_value=mock_consumer_instance), \
         patch("worker.index.PostgresAdapter") as mock_pg, \
         patch("worker.index.RedisAdapter") as mock_redis, \
         patch("worker.index.SlackAdapter") as mock_slack, \
         patch("worker.index.PagerDutyAdapter") as mock_pd, \
         patch("worker.index.PrometheusAdapter") as mock_prom, \
         patch("worker.index.start_http_server"), \
         patch("worker.index._start_health_server"), \
         pytest.raises(StopIteration):
        
        main()

    assert mock_consumer_instance.poll.call_count == 4
    assert mock_consumer_instance.commit.call_count == 2

def test_budget_handler_missing_fields() -> None:
    db = MockDbPort()
    redis = MockRedisPort()
    slack = MockSlackPort()
    metrics = MockMetricsPort()
    handler = BudgetAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        metrics_port=metrics,
        service_owners_path="service_owners.yaml"
    )

    handler.handle({"model": "gpt-4", "event_type": "blocked"})
    assert len(db.calls) == 0

    handler.handle({"user_id": "usr-1", "event_type": "blocked"})
    assert len(db.calls) == 0

    handler.handle({"user_id": "usr-1", "model": "gpt-4"})
    assert len(db.calls) == 0

def test_cost_anomaly_handler_missing_fields() -> None:
    db = MockDbPort()
    redis = MockRedisPort()
    slack = MockSlackPort()
    pd = MockPagerDutyPort()
    metrics = MockMetricsPort()
    handler = CostAnomalyAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        pagerduty_port=pd,
        metrics_port=metrics
    )

    handler.handle({"model": "gpt-4"})
    assert len(db.calls) == 0

    handler.handle({"service": "billing_service"})
    assert len(db.calls) == 0

def test_budget_handler_malformed_datetime() -> None:
    db = MockDbPort()
    redis = MockRedisPort()
    slack = MockSlackPort()
    metrics = MockMetricsPort()
    handler = BudgetAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        metrics_port=metrics,
        service_owners_path="service_owners.yaml"
    )

    handler.handle({
        "user_id": "usr-123",
        "model": "gpt-4",
        "event_type": "blocked",
        "timestamp_utc": "not-a-datetime"
    })
    assert len(db.calls) == 1
    assert db.calls[0]["kwargs"]["delivery_latency_ms"] is None

def test_cost_anomaly_handler_malformed_datetime() -> None:
    db = MockDbPort()
    redis = MockRedisPort()
    slack = MockSlackPort()
    pd = MockPagerDutyPort()
    metrics = MockMetricsPort()
    handler = CostAnomalyAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        pagerduty_port=pd,
        metrics_port=metrics
    )

    handler.handle({
        "service": "billing_service",
        "model": "gpt-4",
        "timestamp": "not-a-datetime"
    })
    assert len(db.calls) == 1
    assert db.calls[0]["kwargs"]["delivery_latency_ms"] is None

def test_cost_anomaly_handler_invalid_types() -> None:
    db = MockDbPort()
    redis = MockRedisPort()
    slack = MockSlackPort()
    pd = MockPagerDutyPort()
    metrics = MockMetricsPort()
    handler = CostAnomalyAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        pagerduty_port=pd,
        metrics_port=metrics
    )

    with pytest.raises(TypeError):
        handler.handle({
            "service": "billing_service",
            "model": "gpt-4",
            "current_cost": "heavy",
            "ewma_value": 2.0,
            "sample_count": 10
        })
