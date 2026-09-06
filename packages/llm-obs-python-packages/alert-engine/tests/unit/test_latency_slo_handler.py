import pytest
from handlers.alerts_latency_slo.handler import LatencySloAlertHandler

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
        self.open_incidents: dict[str, str] = {}

    def acquire_rate_limit(self, key: str, ttl_seconds: int) -> bool:
        self.calls.append({"key": key, "ttl": ttl_seconds})
        return self.allowed

    def get_open_incident(self, model: str, endpoint: str) -> str | None:
        return self.open_incidents.get(f"{model}:{endpoint}")

    def set_open_incident(self, model: str, endpoint: str, incident_id: str, ttl: int) -> None:
        self.open_incidents[f"{model}:{endpoint}"] = incident_id

    def delete_open_incident(self, model: str, endpoint: str) -> None:
        self.open_incidents.pop(f"{model}:{endpoint}", None)

class MockSlackPort:
    def __init__(self) -> None:
        self.channel_calls: list[dict] = []

    def send_channel_message(self, channel: str, text: str) -> None:
        self.channel_calls.append({"channel": channel, "text": text})

    def send_direct_message(self, user: str, text: str) -> None:
        pass

class MockPagerDutyPort:
    def __init__(self) -> None:
        self.incidents: list[dict] = []
        self.resolved_incidents: list[str] = []

    def trigger_incident(
        self,
        summary: str,
        severity: str,
        source: str,
        custom_details: dict | None = None
    ) -> str | None:
        self.incidents.append({
            "summary": summary,
            "severity": severity,
            "source": source,
            "custom_details": custom_details
        })
        return f"mock-pd-incident-{summary}"

    def resolve_incident(self, dedup_key: str) -> None:
        self.resolved_incidents.append(dedup_key)

class MockMetricsPort:
    def __init__(self) -> None:
        self.latency_records: list[dict] = []

    def record_delivery_latency(self, alert_type: str, severity: str, latency_ms: float) -> None:
        self.latency_records.append({
            "alert_type": alert_type,
            "severity": severity,
            "latency_ms": latency_ms
        })


def test_latency_slo_alert_page_success() -> None:
    db = MockDbPort()
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()
    pd = MockPagerDutyPort()
    metrics = MockMetricsPort()

    handler = LatencySloAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        pagerduty_port=pd,
        metrics_port=metrics
    )

    payload = {
        "model": "gpt-4",
        "endpoint": "/v1/chat",
        "severity": "page",
        "burn_rate": 2.5,
        "p95_current": 120.0,
        "p95_baseline": 50.0,
        "p99_current": 250.0,
        "p99_baseline": 100.0,
        "budget_remaining": 88.5,
        "timestamp": "2026-06-29T09:00:00Z"
    }

    handler.handle(payload)

    # Redis rate limit checked
    assert len(redis.calls) == 1
    assert redis.calls[0]["key"] == "rate_limit:latency_slo_page:gpt-4:/v1/chat"
    assert redis.calls[0]["ttl"] == 900

    # PagerDuty triggered
    assert len(pd.incidents) == 1
    assert pd.incidents[0]["summary"] == "Latency SLO breach: gpt-4//v1/chat"
    assert pd.incidents[0]["custom_details"]["burn_rate"] == 2.5
    assert pd.incidents[0]["custom_details"]["budget_remaining"] == 88.5

    # No Slack, No DB write (for page severity, only PD is specified by prompt, though db could be optional)
    assert len(slack.channel_calls) == 0
    assert len(db.inserted) == 0

def test_latency_slo_alert_page_suppressed() -> None:
    db = MockDbPort()
    redis = MockRedisPort(allowed=False)
    slack = MockSlackPort()
    pd = MockPagerDutyPort()
    metrics = MockMetricsPort()

    handler = LatencySloAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        pagerduty_port=pd,
        metrics_port=metrics
    )

    payload = {
        "model": "gpt-4",
        "endpoint": "/v1/chat",
        "severity": "page",
    }

    handler.handle(payload)

    assert len(redis.calls) == 1
    assert len(pd.incidents) == 0

def test_latency_slo_alert_slack() -> None:
    db = MockDbPort()
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()
    pd = MockPagerDutyPort()
    metrics = MockMetricsPort()

    handler = LatencySloAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        pagerduty_port=pd,
        metrics_port=metrics
    )

    payload = {
        "model": "gpt-4",
        "endpoint": "/v1/chat",
        "severity": "slack",
        "burn_rate": 3.2,
        "p95_current": 150.0,
        "p95_baseline": 50.0,
        "p99_current": 300.0,
        "p99_baseline": 100.0,
        "budget_remaining": 75.0,
    }

    handler.handle(payload)

    assert len(slack.channel_calls) == 1
    assert slack.channel_calls[0]["channel"] == "#llm-latency-alerts"
    assert "gpt-4" in slack.channel_calls[0]["text"]
    assert "3.20" in slack.channel_calls[0]["text"]
    assert len(pd.incidents) == 0

def test_latency_slo_alert_ticket() -> None:
    db = MockDbPort()
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()
    pd = MockPagerDutyPort()
    metrics = MockMetricsPort()

    handler = LatencySloAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        pagerduty_port=pd,
        metrics_port=metrics
    )

    payload = {
        "model": "gpt-4",
        "endpoint": "/v1/chat",
        "severity": "ticket",
        "burn_rate": 1.1,
    }

    handler.handle(payload)

    assert len(db.inserted) == 1
    assert db.inserted[0]["alert_type"] == "latency_slo"
    assert db.inserted[0]["service"] == "/v1/chat"
    assert db.inserted[0]["model"] == "gpt-4"
    assert db.inserted[0]["event_type"] == "ticket"
    assert len(slack.channel_calls) == 0
    assert len(pd.incidents) == 0

def test_latency_slo_alert_resolve() -> None:
    db = MockDbPort()
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()
    pd = MockPagerDutyPort()
    metrics = MockMetricsPort()

    handler = LatencySloAlertHandler(
        db_port=db,
        redis_port=redis,
        slack_port=slack,
        pagerduty_port=pd,
        metrics_port=metrics
    )

    # Pre-populate an open incident in MockRedisPort
    redis.open_incidents["gpt-4:/v1/chat"] = "mock-incident-id"

    # Send resolution payload
    payload = {
        "model": "gpt-4",
        "endpoint": "/v1/chat",
        "severity": "None",
    }

    handler.handle(payload)

    # Should resolve the incident
    assert len(pd.resolved_incidents) == 1
    assert pd.resolved_incidents[0] == "mock-incident-id"

    # Should clear Redis tracking key
    assert redis.open_incidents.get("gpt-4:/v1/chat") is None

    # Should post resolution message to Slack
    assert len(slack.channel_calls) == 1
    assert slack.channel_calls[0]["channel"] == "#llm-latency-alerts"
    assert "gpt-4//v1/chat SLO burn rate normalized. Incident auto-resolved." in slack.channel_calls[0]["text"]

