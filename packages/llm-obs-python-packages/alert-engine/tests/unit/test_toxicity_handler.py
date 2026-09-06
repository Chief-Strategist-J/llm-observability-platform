import pytest
from handlers.alerts_toxicity.handler import ToxicityAlertHandler

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

def test_toxicity_alert_success() -> None:
    redis = MockRedisPort(allowed=True)
    slack = MockSlackPort()

    handler = ToxicityAlertHandler(
        redis_port=redis,
        slack_port=slack,
    )

    payload = {
        "span_id": "s-123",
        "user_id": "user-456",
        "model": "toxic-bert",
        "endpoint": "/v1/chat",
        "toxicity_score": 0.85,
    }

    handler.handle(payload)

    assert len(redis.calls) == 1
    assert redis.calls[0]["key"] == "rate_limit:toxicity_alert:user-456:/v1/chat"
    assert redis.calls[0]["ttl"] == 300
    assert len(slack.channel_calls) == 1
    assert slack.channel_calls[0]["channel"] == "#llm-safety-review"
    assert "s-123" in slack.channel_calls[0]["text"]
    assert "0.85" in slack.channel_calls[0]["text"]

def test_toxicity_alert_deduplicated() -> None:
    redis = MockRedisPort(allowed=False)
    slack = MockSlackPort()

    handler = ToxicityAlertHandler(
        redis_port=redis,
        slack_port=slack,
    )

    payload = {
        "span_id": "s-123",
        "user_id": "user-456",
        "model": "toxic-bert",
        "endpoint": "/v1/chat",
        "toxicity_score": 0.85,
    }

    handler.handle(payload)

    assert len(redis.calls) == 1
    assert len(slack.channel_calls) == 0
