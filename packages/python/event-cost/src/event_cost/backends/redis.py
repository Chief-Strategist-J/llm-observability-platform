from datetime import datetime, timezone
import uuid
import redis as redis_lib

from event_cost.backends._base import Backend
from event_cost.ledger import SpanInput

from worker.index import (
    RedisFenwickAdapter,
    RedisTokenBucketAdapter,
    RedisEwmaReaderAdapter,
    RedisDedupAdapter,
)
from handlers.llm_spans_raw.index import process_batch
from handlers.llm_spans_raw.types import RawSpanEvent

class _NoopPriceLookup:
    def get_price(self, model: str, provider: str, version: str):
        return None

class RedisBackend:
    def __init__(self, redis_url: str) -> None:
        self._client = redis_lib.from_url(redis_url)
        self._fenwick = RedisFenwickAdapter(self._client)
        self._bucket = RedisTokenBucketAdapter(self._client)
        self._ewma = RedisEwmaReaderAdapter(self._client)
        self._dedup = RedisDedupAdapter(self._client)
        self._price_lookup = _NoopPriceLookup()

    def record(self, span: SpanInput, cost_usd_micro: int) -> None:
        raw = RawSpanEvent(
            span_id=str(uuid.uuid4()),
            trace_id="",
            service_name=span.service_name,
            model=span.model,
            provider=span.provider,
            prompt_tokens=span.prompt_tokens,
            completion_tokens=span.completion_tokens,
            cost_usd_micro=cost_usd_micro,
            price_version="builtin",
            timestamp_utc=datetime.now(timezone.utc),
            user_id=span.user_id,
            org_id=span.org_id,
            project_id=span.project_id,
            estimated_tokens=span.estimated_tokens,
        )
        process_batch(
            [raw],
            self._fenwick,
            self._bucket,
            self._ewma,
            self._price_lookup,
            self._dedup,
        )

    def query_total(self, org_id: str, window: str, **filters) -> int:
        redis_key = f"fenwick:org:{window}:{org_id}"
        val = self._client.hget(redis_key, "1")
        return int(val) if val else 0

    def get_budget(self, org_id: str, project_id: str) -> int:
        bucket_key = f"budget:tb:{org_id}:{project_id}"
        val = self._client.get(bucket_key)
        return int(val) if val else 0

    def set_budget(self, org_id: str, project_id: str, micro: int) -> None:
        bucket_key = f"budget:tb:{org_id}:{project_id}"
        self._client.set(bucket_key, str(micro))

    def check_anomaly(self, service_name: str, model: str) -> bool:
        return False
