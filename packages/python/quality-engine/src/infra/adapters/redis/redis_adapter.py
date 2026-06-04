from __future__ import annotations
import json
import redis as redis_lib

from shared.ports.baseline_cache_port import BaselineCachePort

_BASELINE_KEY = "baseline:quality:{model}:{endpoint}:{prompt_type}"
_ALERT_RATE_LIMIT_KEY = "rate_limit:quality_alert:{model}:{endpoint}"


class RedisBaselineCacheAdapter(BaselineCachePort):
    """
    F-Q-07 / F-Q-08 Redis adapter.
    Baseline values stored as JSON envelopes for schema-safe reads.
    TTL default: 8 days (691200 seconds) per F-Q-07 spec.
    """

    def __init__(self, url: str) -> None:
        self._client = redis_lib.from_url(url, decode_responses=True)

    def get_baseline(self, model: str, endpoint: str, prompt_type: str) -> float | None:
        key = _BASELINE_KEY.format(model=model, endpoint=endpoint, prompt_type=prompt_type)
        raw = self._client.get(key)
        if raw is None:
            return None
        try:
            envelope = json.loads(raw)
            return float(envelope["value"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def set_baseline(
        self,
        model: str,
        endpoint: str,
        prompt_type: str,
        value: float,
        ttl_seconds: int = 691200,
    ) -> None:
        key = _BASELINE_KEY.format(model=model, endpoint=endpoint, prompt_type=prompt_type)
        import datetime
        envelope = json.dumps({
            "value": value,
            "schema_version": 1,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        })
        self._client.set(key, envelope, ex=ttl_seconds)

    def is_alert_rate_limited(self, model: str, endpoint: str) -> bool:
        key = _ALERT_RATE_LIMIT_KEY.format(model=model, endpoint=endpoint)
        return self._client.exists(key) == 1

    def set_alert_rate_limit(self, model: str, endpoint: str, ttl_seconds: int = 3600) -> None:
        key = _ALERT_RATE_LIMIT_KEY.format(model=model, endpoint=endpoint)
        self._client.set(key, "1", ex=ttl_seconds)
