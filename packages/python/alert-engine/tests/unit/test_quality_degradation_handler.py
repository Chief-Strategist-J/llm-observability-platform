import logging
import pytest
from handlers.alerts_quality_degradation.handler import QualityDegradationAlertHandler


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


_VALID_PAYLOAD: dict = {
    "model": "gpt-4o",
    "endpoint": "/v1/chat/completions",
    "current_window_avg": 0.61,
    "baseline": 0.80,
    "ratio": 0.7625,
    "alerted_at": "2026-06-15T08:00:00+00:00",
}


def test_degradation_alert_success_sends_slack() -> None:
    """Non-cold-start alert with rate limit acquired → Slack message sent."""
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()

    handler = QualityDegradationAlertHandler(redis_port=redis, slack_port=slack)
    handler.handle({**_VALID_PAYLOAD, "is_cold_start": False})

    assert len(redis.calls) == 1
    assert redis.calls[0]["key"] == "rate_limit:quality_degradation:gpt-4o:/v1/chat/completions"
    assert redis.calls[0]["ttl"] == 3600
    assert len(slack.channel_calls) == 1
    assert slack.channel_calls[0]["channel"] == "#llm-quality-alerts"
    msg = slack.channel_calls[0]["text"]
    assert "gpt-4o" in msg
    assert "/v1/chat/completions" in msg
    assert "0.6100" in msg
    assert "0.8000" in msg
    assert "0.7625" in msg


def test_degradation_alert_cold_start_suppresses_slack(caplog) -> None:
    """Cold-start payload → no Slack alert; warning logged."""
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()

    handler = QualityDegradationAlertHandler(redis_port=redis, slack_port=slack)
    with caplog.at_level(logging.WARNING):
        handler.handle({**_VALID_PAYLOAD, "is_cold_start": True})

    # Redis dedup should NOT be called (we return early before rate-limit check)
    assert len(redis.calls) == 0
    # No Slack message
    assert len(slack.channel_calls) == 0
    # Warning logged
    assert any("cold-start" in record.message for record in caplog.records)


def test_degradation_alert_missing_fields_no_crash() -> None:
    """Payload missing required fields → handler returns without crashing."""
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()

    handler = QualityDegradationAlertHandler(redis_port=redis, slack_port=slack)
    # Completely empty payload
    handler.handle({})

    assert len(redis.calls) == 0
    assert len(slack.channel_calls) == 0


def test_degradation_alert_partial_missing_fields_no_crash() -> None:
    """Payload missing some required fields → handler returns without crashing."""
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()

    handler = QualityDegradationAlertHandler(redis_port=redis, slack_port=slack)
    handler.handle({"model": "gpt-4o"})  # missing endpoint, averages, etc.

    assert len(redis.calls) == 0
    assert len(slack.channel_calls) == 0


def test_degradation_alert_rate_limited_suppresses_second() -> None:
    """When rate limit already acquired (second call) → Slack suppressed."""
    redis = MockRedisPort(allowed=False)  # rate limit not acquirable
    slack = MockSlackPort()

    handler = QualityDegradationAlertHandler(redis_port=redis, slack_port=slack)
    handler.handle({**_VALID_PAYLOAD, "is_cold_start": False})

    assert len(redis.calls) == 1
    assert len(slack.channel_calls) == 0


def test_degradation_alert_default_cold_start_is_false() -> None:
    """is_cold_start defaults to False when not in payload → Slack sent normally."""
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()

    handler = QualityDegradationAlertHandler(redis_port=redis, slack_port=slack)
    # Payload without is_cold_start key
    handler.handle(_VALID_PAYLOAD)

    assert len(slack.channel_calls) == 1
    assert slack.channel_calls[0]["channel"] == "#llm-quality-alerts"


def test_degradation_alert_rate_limit_key_format() -> None:
    """Verify the rate limit key includes model and endpoint correctly."""
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()

    handler = QualityDegradationAlertHandler(redis_port=redis, slack_port=slack)
    handler.handle({
        **_VALID_PAYLOAD,
        "model": "claude-3",
        "endpoint": "/api/infer",
        "is_cold_start": False,
    })

    assert redis.calls[0]["key"] == "rate_limit:quality_degradation:claude-3:/api/infer"
    assert redis.calls[0]["ttl"] == 3600
