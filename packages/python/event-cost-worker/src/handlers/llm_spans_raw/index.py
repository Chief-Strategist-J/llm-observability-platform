import logging
from typing import Protocol
from handlers.llm_spans_raw.types import (
    RawSpanEvent,
    FenwickUpdate,
    HandlerResult,
)
from handlers.llm_spans_raw import handler
from shared.types.cost_types import PriceEntry

logger = logging.getLogger(__name__)

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

DEDUP_TTL_SECONDS = 3600


from shared.ports.metrics_port import MetricsPort

class FenwickAdapter(Protocol):
    def pipeline_update(self, updates: list[FenwickUpdate], metrics: MetricsPort | None = None) -> None: ...


class TokenBucketAdapter(Protocol):
    def deduct(self, bucket_key: str, delta: int) -> int: ...


class EwmaReaderAdapter(Protocol):
    def get_ewma(self, service: str, model: str, hour_of_week: int) -> float | None: ...


class PriceLookupAdapter(Protocol):
    def get_price(self, model: str, provider: str, version: str) -> PriceEntry | None: ...


class DedupAdapter(Protocol):
    def is_new(self, span_id: str) -> bool: ...


def _hour_of_week(span: RawSpanEvent) -> int:
    dt = span.timestamp_utc
    return dt.weekday() * 24 + dt.hour


def process_span(
    span: RawSpanEvent,
    fenwick: FenwickAdapter,
    bucket: TokenBucketAdapter,
    ewma: EwmaReaderAdapter,
    price_lookup: PriceLookupAdapter,
    dedup: DedupAdapter,
    metrics: MetricsPort | None = None,
) -> bool:
    if not dedup.is_new(span.span_id):
        logger.info("duplicate span_id=%s skipped", span.span_id)
        return False

    updates = handler.build_fenwick_updates(span)
    fenwick.pipeline_update(updates, metrics)

    delta = handler.compute_token_bucket_delta(span)
    if delta is not None:
        bucket.deduct(delta.bucket_key, delta.delta_tokens)

    price = price_lookup.get_price(span.model, span.provider, span.price_version)
    is_mismatch = handler.reconcile_price(span, price)
    if is_mismatch:
        logger.warning(
            "cost_reconciliation_mismatch span_id=%s model=%s",
            span.span_id,
            span.model,
        )

    ewma_val = ewma.get_ewma(
        span.service_name, span.model, _hour_of_week(span)
    )
    burn = handler.compute_burn_ratio(span.cost_usd_micro, ewma_val)
    if burn is not None:
        logger.info(
            "burn_ratio span_id=%s ratio=%.4f",
            span.span_id,
            burn,
        )

    if metrics is not None:
        metrics.record_processed_span(span.service_name, span.model)

    return is_mismatch


def process_batch(
    spans: list[RawSpanEvent],
    fenwick: FenwickAdapter,
    bucket: TokenBucketAdapter,
    ewma: EwmaReaderAdapter,
    price_lookup: PriceLookupAdapter,
    dedup: DedupAdapter,
    metrics: MetricsPort | None = None,
) -> HandlerResult:
    result = HandlerResult()
    for span in spans:
        is_mismatch = process_span(span, fenwick, bucket, ewma, price_lookup, dedup, metrics)
        result.processed_count += 1
        if is_mismatch:
            result.mismatch_count += 1
    return result
