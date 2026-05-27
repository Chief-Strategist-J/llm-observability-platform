from datetime import datetime, timezone
import uuid
import redis as redis_lib

from event_cost.backends._base import Backend
from event_cost.ledger import SpanInput

FENWICK_UPDATE_LUA = """
local key = KEYS[1]
local delta = tonumber(ARGV[1])
local i = tonumber(ARGV[2])
local n = tonumber(ARGV[3])
while i <= n do
    redis.call('HINCRBY', key, tostring(i), delta)
    i = i + bit.band(i, -i)
end
return 1
"""

FENWICK_QUERY_LUA = """
local key = KEYS[1]
local i = tonumber(ARGV[1])
local sum = 0
while i > 0 do
    sum = sum + tonumber(redis.call('HGET', key, tostring(i)) or '0')
    i = i - bit.band(i, -i)
end
return sum
"""

TOKEN_BUCKET_DEDUCT_LUA = """
local key = KEYS[1]
local delta = tonumber(ARGV[1])
local current = tonumber(redis.call('GET', key) or '0')
local new_val = current - delta
redis.call('SET', key, tostring(new_val))
return new_val
"""

DEDUP_CHECK_LUA = """
local key = KEYS[1]
local span_id = ARGV[1]
local ttl = tonumber(ARGV[2])
local added = redis.call('SADD', key, span_id)
if added == 1 then
    redis.call('EXPIRE', key, ttl)
    return 1
end
return 0
"""

DIMENSIONS = ("org", "project", "service", "model", "user")
WINDOWS = ("1h", "24h", "7d", "30d")

class _FenwickUpdate:
    def __init__(self, dimension: str, window: str, key: str, delta: int) -> None:
        self.dimension = dimension
        self.window = window
        self.key = key
        self.delta = delta

class RedisFenwickAdapter:
    def __init__(self, client: redis_lib.Redis) -> None:
        self._client = client
        self._script = self._client.register_script(FENWICK_UPDATE_LUA)

    def pipeline_update(self, updates: list[_FenwickUpdate]) -> None:
        pipe = self._client.pipeline(transaction=False)
        for u in updates:
            redis_key = f"fenwick:{u.dimension}:{u.window}:{u.key}"
            n = 1024
            i = 1
            pipe.evalsha(
                self._script.sha,
                1,
                redis_key,
                str(u.delta),
                str(i),
                str(n),
            )
        pipe.execute()

class RedisTokenBucketAdapter:
    def __init__(self, client: redis_lib.Redis) -> None:
        self._client = client
        self._script = self._client.register_script(TOKEN_BUCKET_DEDUCT_LUA)

    def deduct(self, bucket_key: str, delta: int) -> int:
        result = self._script(keys=[bucket_key], args=[str(delta)])
        return int(result)

class RedisDedupAdapter:
    def __init__(self, client: redis_lib.Redis) -> None:
        self._client = client
        self._script = self._client.register_script(DEDUP_CHECK_LUA)

    def is_new(self, span_id: str) -> bool:
        result = self._script(
            keys=["dedup:cost_engine"],
            args=[span_id, "3600"],
        )
        return int(result) == 1

class RedisBackend:
    def __init__(self, redis_url: str) -> None:
        self._client = redis_lib.from_url(redis_url)
        self._fenwick = RedisFenwickAdapter(self._client)
        self._bucket = RedisTokenBucketAdapter(self._client)
        self._dedup = RedisDedupAdapter(self._client)
        self._query_script = self._client.register_script(FENWICK_QUERY_LUA)

    def record(self, span: SpanInput, cost_usd_micro: int) -> None:
        span_id = str(uuid.uuid4())
        if not self._dedup.is_new(span_id):
            return

        dim_keys = {
            "org": span.org_id,
            "project": span.project_id,
            "service": span.service_name,
            "model": span.model,
            "user": span.user_id,
        }
        updates = []
        for dim in DIMENSIONS:
            for win in WINDOWS:
                updates.append(
                    _FenwickUpdate(
                        dimension=dim,
                        window=win,
                        key=dim_keys[dim],
                        delta=cost_usd_micro,
                    )
                )
        self._fenwick.pipeline_update(updates)

        if span.estimated_tokens > 0:
            overshoot = span.completion_tokens - span.estimated_tokens
            if overshoot > 0:
                bucket_key = f"budget:tb:{span.org_id}:{span.project_id}"
                self._bucket.deduct(bucket_key, overshoot)

    def query_total(self, org_id: str, window: str, **filters) -> int:
        redis_key = f"fenwick:org:{window}:{org_id}"
        result = self._query_script(keys=[redis_key], args=["1024"])
        return int(result) if result else 0

    def get_budget(self, org_id: str, project_id: str) -> int:
        bucket_key = f"budget:tb:{org_id}:{project_id}"
        val = self._client.get(bucket_key)
        return int(val) if val else 0

    def set_budget(self, org_id: str, project_id: str, micro: int) -> None:
        bucket_key = f"budget:tb:{org_id}:{project_id}"
        self._client.set(bucket_key, str(micro))

    def check_anomaly(self, service_name: str, model: str) -> bool:
        return False
