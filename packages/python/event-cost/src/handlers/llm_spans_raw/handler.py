from handlers.llm_spans_raw.types import (
    RawSpanEvent,
    FenwickUpdate,
    TokenBucketDelta,
)
from shared.types.cost_types import PriceEntry

DIMENSIONS = ("org", "project", "service", "model", "user")
WINDOWS = ("1h", "24h", "7d", "30d")


def build_fenwick_updates(span: RawSpanEvent) -> list[FenwickUpdate]:
    dim_keys = {
        "org": span.org_id,
        "project": span.project_id,
        "service": span.service_name,
        "model": span.model,
        "user": span.user_id,
    }
    updates: list[FenwickUpdate] = []
    for dim in DIMENSIONS:
        for win in WINDOWS:
            updates.append(
                FenwickUpdate(
                    dimension=dim,
                    window=win,
                    key=dim_keys[dim],
                    delta=span.cost_usd_micro,
                )
            )
    return updates


def compute_token_bucket_delta(
    span: RawSpanEvent,
) -> TokenBucketDelta | None:
    if span.estimated_tokens <= 0:
        return None
    overshoot = span.completion_tokens - span.estimated_tokens
    if overshoot <= 0:
        return None
    bucket_key = f"budget:tb:{span.org_id}:{span.project_id}"
    return TokenBucketDelta(bucket_key=bucket_key, delta_tokens=overshoot)


def reconcile_price(
    span: RawSpanEvent,
    price: PriceEntry | None,
) -> bool:
    if price is None:
        return False
    expected = (
        span.prompt_tokens * price.input_price_per_token_micro
        + span.completion_tokens * price.output_price_per_token_micro
    )
    if expected == 0:
        return span.cost_usd_micro != 0
    ratio = abs(span.cost_usd_micro - expected) / expected
    return ratio > 0.02


def compute_burn_ratio(
    cost_usd_micro: int,
    ewma_value: float | None,
) -> float | None:
    if ewma_value is None or ewma_value <= 0:
        return None
    return cost_usd_micro / ewma_value
