import pytest
from handlers.alerts_cost_anomaly.handler import CostAnomalyAlertHandler

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

    def send_channel_message(self, channel: str, text: str) -> None:
        self.channel_calls.append({"channel": channel, "text": text})

    def send_direct_message(self, user: str, text: str) -> None:
        pass

class MockPagerDutyPort:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def trigger_incident(
        self,
        summary: str,
        severity: str,
        source: str,
        custom_details: dict | None = None
    ) -> None:
        self.calls.append({
            "summary": summary,
            "severity": severity,
            "source": source,
            "custom_details": custom_details
        })

class MockMetricsPort:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def record_delivery_latency(self, alert_type: str, severity: str, latency_ms: float) -> None:
        self.calls.append({"alert_type": alert_type, "severity": severity, "latency_ms": latency_ms})

def test_cost_anomaly_cold_start() -> None:
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

    payload = {
        "service": "billing_service",
        "model": "gpt-4",
        "sample_count": 5,
        "current_cost": 10.0,
        "ewma_value": 2.0,
        "threshold_value": 6.0,
        "timestamp": "2026-05-28T10:00:00Z",
        "cluster_drilldown": []
    }

    handler.handle(payload)

    assert len(db.calls) == 1
    assert db.calls[0]["event_type"] == "cold_start"
    assert len(slack.channel_calls) == 0
    assert len(pd.calls) == 0
    assert len(metrics.calls) == 1
    assert metrics.calls[0]["severity"] == "info"

def test_cost_anomaly_spike() -> None:
    db = MockDbPort()
    redis = MockRedisPort(allowed=True)
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

    payload = {
        "service": "billing_service",
        "model": "gpt-4",
        "sample_count": 10,
        "current_cost": 12.0,
        "ewma_value": 2.0,
        "threshold_value": 6.0,
        "timestamp": "2026-05-28T10:00:00Z",
        "cluster_drilldown": [
            {"cluster_id": "prompt-injection", "cost": 9.0},
            {"cluster_id": "other-queries", "cost": 3.0}
        ]
    }

    handler.handle(payload)

    assert len(redis.calls) == 1
    assert redis.calls[0]["key"] == "rate_limit:cost_anomaly:billing_service:gpt-4"
    assert len(db.calls) == 1
    assert db.calls[0]["event_type"] == "spike"
    assert len(slack.channel_calls) == 1
    assert "prompt-injection" in slack.channel_calls[0]["text"]
    assert len(pd.calls) == 1
    assert pd.calls[0]["severity"] == "critical"
    assert len(metrics.calls) == 1
    assert metrics.calls[0]["severity"] == "critical"

def test_cost_anomaly_spike_rate_limited() -> None:
    db = MockDbPort()
    redis = MockRedisPort(allowed=False)
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

    payload = {
        "service": "billing_service",
        "model": "gpt-4",
        "sample_count": 10,
        "current_cost": 12.0,
        "ewma_value": 2.0,
        "threshold_value": 6.0,
        "timestamp": "2026-05-28T10:00:00Z",
        "cluster_drilldown": []
    }

    handler.handle(payload)

    assert len(redis.calls) == 1
    assert len(db.calls) == 0
    assert len(slack.channel_calls) == 0
    assert len(pd.calls) == 0
    assert len(metrics.calls) == 0
