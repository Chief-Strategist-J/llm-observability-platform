import pytest
from unittest.mock import MagicMock
from handlers.alerts_budget.handler import BudgetAlertHandler

class MockDbPort:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def insert_alert(
        self,
        alert_type: str,
        service: str | None,
        model: str | None,
        user_id: str | None,
        event_type: str | None,
        payload: dict,
        delivery_latency_ms: int | None
    ) -> None:
        self.calls.append({
            "alert_type": alert_type,
            "service": service,
            "model": model,
            "user_id": user_id,
            "event_type": event_type,
            "payload": payload,
            "delivery_latency_ms": delivery_latency_ms
        })

class MockRedisPort:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed
        self.calls: list[dict] = []

    def acquire_rate_limit(self, key: str, ttl_seconds: int) -> bool:
        self.calls.append({"key": key, "ttl": ttl_seconds})
        return self.allowed

class MockSlackPort:
    def __init__(self) -> None:
        self.channel_calls: list[dict] = []
        self.dm_calls: list[dict] = []

    def send_channel_message(self, channel: str, text: str) -> None:
        self.channel_calls.append({"channel": channel, "text": text})

    def send_direct_message(self, user: str, text: str) -> None:
        self.dm_calls.append({"user": user, "text": text})

class MockMetricsPort:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def record_delivery_latency(self, alert_type: str, severity: str, latency_ms: float) -> None:
        self.calls.append({"alert_type": alert_type, "severity": severity, "latency_ms": latency_ms})

@pytest.fixture
def service_owners_file(tmp_path) -> str:
    yaml_content = """
service_owners:
  billing_service: "@john-billing"
  recommendation_service: "@sarah-recs"
"""
    file_path = tmp_path / "service_owners.yaml"
    file_path.write_text(yaml_content)
    return str(file_path)

def test_budget_blocked(service_owners_file) -> None:
    db = MockDbPort()
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()
    metrics = MockMetricsPort()

    handler = BudgetAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        metrics_port=metrics,
        service_owners_path=service_owners_file
    )

    payload = {
        "user_id": "usr-123",
        "model": "gpt-4",
        "event_type": "blocked",
        "timestamp_utc": "2026-05-28T10:00:00Z",
        "service": "billing_service"
    }

    handler.handle(payload)

    assert len(redis.calls) == 1
    assert redis.calls[0]["key"] == "rate_limit:budget_alert:usr-123:gpt-4"
    assert len(db.calls) == 1
    assert db.calls[0]["event_type"] == "blocked"
    assert db.calls[0]["user_id"] == "usr-123"
    assert len(slack.channel_calls) == 1
    assert slack.channel_calls[0]["channel"] == "#llm-cost-alerts"
    assert len(metrics.calls) == 1
    assert metrics.calls[0]["severity"] == "critical"

def test_budget_warning_80pct(service_owners_file) -> None:
    db = MockDbPort()
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()
    metrics = MockMetricsPort()

    handler = BudgetAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        metrics_port=metrics,
        service_owners_path=service_owners_file
    )

    payload = {
        "user_id": "usr-123",
        "model": "gpt-4",
        "event_type": "warning_80pct",
        "timestamp_utc": "2026-05-28T10:00:00Z",
        "service": "recommendation_service"
    }

    handler.handle(payload)

    assert len(db.calls) == 1
    assert db.calls[0]["event_type"] == "warning_80pct"
    assert len(slack.dm_calls) == 1
    assert slack.dm_calls[0]["user"] == "@sarah-recs"
    assert len(metrics.calls) == 1
    assert metrics.calls[0]["severity"] == "warning"

def test_budget_rate_limited(service_owners_file) -> None:
    db = MockDbPort()
    redis = MockRedisPort(allowed=False)
    slack = MockSlackPort()
    metrics = MockMetricsPort()

    handler = BudgetAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        metrics_port=metrics,
        service_owners_path=service_owners_file
    )

    payload = {
        "user_id": "usr-123",
        "model": "gpt-4",
        "event_type": "blocked",
        "timestamp_utc": "2026-05-28T10:00:00Z",
        "service": "billing_service"
    }

    handler.handle(payload)

    assert len(redis.calls) == 1
    assert len(db.calls) == 0
    assert len(slack.channel_calls) == 0
    assert len(metrics.calls) == 0
