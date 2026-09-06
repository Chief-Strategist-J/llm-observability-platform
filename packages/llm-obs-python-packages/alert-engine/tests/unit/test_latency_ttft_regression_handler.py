import pytest
from handlers.alerts_latency_ttft_regression.handler import LatencyTtftRegressionAlertHandler

class MockDbPort:
    def __init__(self) -> None:
        self.inserted: list[dict] = []

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
        self.inserted.append({
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

    def send_channel_message(self, channel: str, text: str) -> None:
        self.channel_calls.append({"channel": channel, "text": text})

class MockMetricsPort:
    def __init__(self) -> None:
        self.latency_records: list[dict] = []

    def record_delivery_latency(self, alert_type: str, severity: str, latency_ms: float) -> None:
        self.latency_records.append({
            "alert_type": alert_type,
            "severity": severity,
            "latency_ms": latency_ms
        })

def test_latency_ttft_regression_success() -> None:
    db = MockDbPort()
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()
    metrics = MockMetricsPort()

    handler = LatencyTtftRegressionAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        metrics_port=metrics
    )

    payload = {
        "model": "gemini-1.5-flash",
        "current": 180.0,
        "baseline": 120.0,
        "hour_of_day": 14,
        "timestamp": "2026-07-01T14:00:00Z"
    }

    handler.handle(payload)

    # Redis rate limit checked (key: model and hour_of_day, 6 hours TTL)
    assert len(redis.calls) == 1
    assert redis.calls[0]["key"] == "rate_limit:latency_ttft_regression:gemini-1.5-flash:14"
    assert redis.calls[0]["ttl"] == 21600

    # DB write should exist
    assert len(db.inserted) == 1
    assert db.inserted[0]["alert_type"] == "latency_ttft_regression"
    assert db.inserted[0]["model"] == "gemini-1.5-flash"
    assert db.inserted[0]["payload"]["current"] == 180.0
    assert db.inserted[0]["payload"]["baseline"] == 120.0
    assert db.inserted[0]["payload"]["hour_of_day"] == 14

    # Slack channel message sent
    assert len(slack.channel_calls) == 1
    assert slack.channel_calls[0]["channel"] == "#llm-latency-alerts"
    assert slack.channel_calls[0]["text"] == "gemini-1.5-flash TTFT P99 degraded: 180.0ms vs 120.0ms baseline at 14:00 UTC. Possible provider degradation."

def test_latency_ttft_regression_rate_limited() -> None:
    db = MockDbPort()
    redis = MockRedisPort(allowed=False)
    slack = MockSlackPort()
    metrics = MockMetricsPort()

    handler = LatencyTtftRegressionAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        metrics_port=metrics
    )

    payload = {
        "model": "gemini-1.5-flash",
        "current": 180.0,
        "baseline": 120.0,
        "hour_of_day": 14,
        "timestamp": "2026-07-01T14:00:00Z"
    }

    handler.handle(payload)

    assert len(redis.calls) == 1
    assert len(db.inserted) == 0
    assert len(slack.channel_calls) == 0
