import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call
from dataclasses import dataclass
import pytest

from handlers.llm_spans_raw.handler import (
    build_fenwick_updates,
    compute_token_bucket_delta,
    reconcile_price,
    compute_burn_ratio,
    DIMENSIONS,
    WINDOWS,
)
from handlers.llm_spans_raw.index import (
    process_span,
    process_batch,
    _hour_of_week,
)
from handlers.llm_spans_raw.types import RawSpanEvent, HandlerResult
from shared.types.cost_types import PriceEntry


def _make_span(**overrides) -> RawSpanEvent:
    defaults = {
        "span_id": "aaa-111",
        "trace_id": "bbb-222",
        "service_name": "chat-api",
        "model": "gpt-4",
        "provider": "openai",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "cost_usd_micro": 1500,
        "price_version": "v1",
        "timestamp_utc": datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc),
        "user_id": "user-1",
        "org_id": "org-1",
        "project_id": "proj-1",
        "estimated_tokens": 40,
    }
    defaults.update(overrides)
    return RawSpanEvent(**defaults)


class TestBuildFenwickUpdates:
    def test_returns_20_updates(self) -> None:
        span = _make_span()
        updates = build_fenwick_updates(span)
        assert len(updates) == 20

    def test_dimensions_and_windows(self) -> None:
        span = _make_span()
        updates = build_fenwick_updates(span)
        dims = {u.dimension for u in updates}
        wins = {u.window for u in updates}
        assert dims == {"org", "project", "service", "model", "user"}
        assert wins == {"1h", "24h", "7d", "30d"}

    def test_delta_equals_cost(self) -> None:
        span = _make_span(cost_usd_micro=2000)
        updates = build_fenwick_updates(span)
        for u in updates:
            assert u.delta == 2000

    def test_key_mapping(self) -> None:
        span = _make_span(org_id="org-x", model="gpt-4")
        updates = build_fenwick_updates(span)
        org_updates = [u for u in updates if u.dimension == "org"]
        for u in org_updates:
            assert u.key == "org-x"
        model_updates = [u for u in updates if u.dimension == "model"]
        for u in model_updates:
            assert u.key == "gpt-4"

    def test_zero_cost_produces_zero_deltas(self) -> None:
        span = _make_span(cost_usd_micro=0)
        updates = build_fenwick_updates(span)
        assert all(u.delta == 0 for u in updates)

    def test_empty_user_id_still_produces_updates(self) -> None:
        span = _make_span(user_id="")
        updates = build_fenwick_updates(span)
        user_updates = [u for u in updates if u.dimension == "user"]
        assert len(user_updates) == 4
        assert all(u.key == "" for u in user_updates)

    def test_negative_cost_produces_negative_deltas(self) -> None:
        span = _make_span(cost_usd_micro=-500)
        updates = build_fenwick_updates(span)
        assert all(u.delta == -500 for u in updates)

    def test_each_dimension_has_all_four_windows(self) -> None:
        span = _make_span()
        updates = build_fenwick_updates(span)
        for dim in DIMENSIONS:
            dim_wins = {u.window for u in updates if u.dimension == dim}
            assert dim_wins == set(WINDOWS)


class TestComputeTokenBucketDelta:
    def test_overshoot_returns_delta(self) -> None:
        span = _make_span(completion_tokens=60, estimated_tokens=40)
        result = compute_token_bucket_delta(span)
        assert result is not None
        assert result.delta_tokens == 20
        assert result.bucket_key == "budget:tb:org-1:proj-1"

    def test_no_overshoot_returns_none(self) -> None:
        span = _make_span(completion_tokens=30, estimated_tokens=40)
        assert compute_token_bucket_delta(span) is None

    def test_zero_estimated_returns_none(self) -> None:
        span = _make_span(estimated_tokens=0)
        assert compute_token_bucket_delta(span) is None

    def test_exact_match_returns_none(self) -> None:
        span = _make_span(completion_tokens=40, estimated_tokens=40)
        assert compute_token_bucket_delta(span) is None

    def test_negative_estimated_returns_none(self) -> None:
        span = _make_span(estimated_tokens=-1)
        assert compute_token_bucket_delta(span) is None

    def test_large_overshoot(self) -> None:
        span = _make_span(completion_tokens=10000, estimated_tokens=1)
        result = compute_token_bucket_delta(span)
        assert result is not None
        assert result.delta_tokens == 9999

    def test_bucket_key_format(self) -> None:
        span = _make_span(org_id="acme", project_id="prod")
        result = compute_token_bucket_delta(span)
        assert result is not None
        assert result.bucket_key == "budget:tb:acme:prod"


class TestReconcilePrice:
    def test_no_price_returns_false(self) -> None:
        span = _make_span()
        assert reconcile_price(span, None) is False

    def test_matching_price_returns_false(self) -> None:
        span = _make_span(
            prompt_tokens=100,
            completion_tokens=50,
            cost_usd_micro=1500,
        )
        price = PriceEntry(
            model="gpt-4",
            provider="openai",
            input_price_per_token_micro=10,
            output_price_per_token_micro=10,
            version="v1",
        )
        assert reconcile_price(span, price) is False

    def test_large_mismatch_returns_true(self) -> None:
        span = _make_span(
            prompt_tokens=100,
            completion_tokens=50,
            cost_usd_micro=9999,
        )
        price = PriceEntry(
            model="gpt-4",
            provider="openai",
            input_price_per_token_micro=10,
            output_price_per_token_micro=10,
            version="v1",
        )
        assert reconcile_price(span, price) is True

    def test_within_2_percent_tolerance_returns_false(self) -> None:
        span = _make_span(
            prompt_tokens=100,
            completion_tokens=50,
            cost_usd_micro=1520,
        )
        price = PriceEntry(
            model="gpt-4",
            provider="openai",
            input_price_per_token_micro=10,
            output_price_per_token_micro=10,
            version="v1",
        )
        assert reconcile_price(span, price) is False

    def test_exactly_2_percent_boundary_returns_false(self) -> None:
        expected = 1500
        span = _make_span(cost_usd_micro=expected + int(expected * 0.02))
        price = PriceEntry(
            model="gpt-4",
            provider="openai",
            input_price_per_token_micro=10,
            output_price_per_token_micro=10,
            version="v1",
        )
        assert reconcile_price(span, price) is False

    def test_zero_expected_cost_with_nonzero_actual(self) -> None:
        span = _make_span(
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd_micro=100,
        )
        price = PriceEntry(
            model="gpt-4",
            provider="openai",
            input_price_per_token_micro=10,
            output_price_per_token_micro=10,
            version="v1",
        )
        assert reconcile_price(span, price) is True

    def test_zero_expected_cost_with_zero_actual(self) -> None:
        span = _make_span(
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd_micro=0,
        )
        price = PriceEntry(
            model="gpt-4",
            provider="openai",
            input_price_per_token_micro=10,
            output_price_per_token_micro=10,
            version="v1",
        )
        assert reconcile_price(span, price) is False


class TestComputeBurnRatio:
    def test_valid_ratio(self) -> None:
        assert compute_burn_ratio(2000, 1000.0) == 2.0

    def test_none_ewma_returns_none(self) -> None:
        assert compute_burn_ratio(2000, None) is None

    def test_zero_ewma_returns_none(self) -> None:
        assert compute_burn_ratio(2000, 0.0) is None

    def test_negative_ewma_returns_none(self) -> None:
        assert compute_burn_ratio(2000, -1.0) is None

    def test_zero_cost_returns_zero_ratio(self) -> None:
        assert compute_burn_ratio(0, 100.0) == 0.0

    def test_fractional_ratio(self) -> None:
        result = compute_burn_ratio(500, 1000.0)
        assert result == pytest.approx(0.5)


class TestHourOfWeek:
    def test_monday_midnight(self) -> None:
        dt = datetime(2026, 5, 25, 0, 0, 0, tzinfo=timezone.utc)
        span = _make_span(timestamp_utc=dt)
        assert _hour_of_week(span) == 0

    def test_tuesday_noon(self) -> None:
        dt = datetime(2026, 5, 26, 12, 0, 0, tzinfo=timezone.utc)
        span = _make_span(timestamp_utc=dt)
        assert _hour_of_week(span) == 1 * 24 + 12

    def test_sunday_23h(self) -> None:
        dt = datetime(2026, 5, 31, 23, 0, 0, tzinfo=timezone.utc)
        span = _make_span(timestamp_utc=dt)
        assert _hour_of_week(span) == 6 * 24 + 23


class TestProcessSpanOrchestrator:
    def _make_fakes(self):
        fenwick = MagicMock()
        bucket = MagicMock()
        ewma = MagicMock()
        ewma.get_ewma.return_value = 1000.0
        price = MagicMock()
        price.get_price.return_value = PriceEntry(
            model="gpt-4", provider="openai",
            input_price_per_token_micro=10,
            output_price_per_token_micro=10,
            version="v1",
        )
        dedup = MagicMock()
        dedup.is_new.return_value = True
        return fenwick, bucket, ewma, price, dedup

    def test_calls_fenwick_with_20_updates(self) -> None:
        fenwick, bucket, ewma, price, dedup = self._make_fakes()
        span = _make_span()
        process_span(span, fenwick, bucket, ewma, price, dedup)
        fenwick.pipeline_update.assert_called_once()
        updates = fenwick.pipeline_update.call_args[0][0]
        assert len(updates) == 20

    def test_calls_bucket_deduct_on_overshoot(self) -> None:
        fenwick, bucket, ewma, price, dedup = self._make_fakes()
        span = _make_span(completion_tokens=60, estimated_tokens=40)
        process_span(span, fenwick, bucket, ewma, price, dedup)
        bucket.deduct.assert_called_once_with("budget:tb:org-1:proj-1", 20)

    def test_skips_bucket_deduct_when_no_overshoot(self) -> None:
        fenwick, bucket, ewma, price, dedup = self._make_fakes()
        span = _make_span(completion_tokens=30, estimated_tokens=40)
        process_span(span, fenwick, bucket, ewma, price, dedup)
        bucket.deduct.assert_not_called()

    def test_duplicate_span_skipped(self) -> None:
        fenwick, bucket, ewma, price, dedup = self._make_fakes()
        dedup.is_new.return_value = False
        span = _make_span()
        process_span(span, fenwick, bucket, ewma, price, dedup)
        fenwick.pipeline_update.assert_not_called()
        bucket.deduct.assert_not_called()

    def test_returns_true_on_price_mismatch(self) -> None:
        fenwick, bucket, ewma, price, dedup = self._make_fakes()
        span = _make_span(cost_usd_micro=9999)
        result = process_span(span, fenwick, bucket, ewma, price, dedup)
        assert result is True

    def test_returns_false_on_match(self) -> None:
        fenwick, bucket, ewma, price, dedup = self._make_fakes()
        span = _make_span(cost_usd_micro=1500)
        result = process_span(span, fenwick, bucket, ewma, price, dedup)
        assert result is False


class TestProcessBatch:
    def _make_fakes(self):
        fenwick = MagicMock()
        bucket = MagicMock()
        ewma = MagicMock()
        ewma.get_ewma.return_value = 1000.0
        price = MagicMock()
        price.get_price.return_value = PriceEntry(
            model="gpt-4", provider="openai",
            input_price_per_token_micro=10,
            output_price_per_token_micro=10,
            version="v1",
        )
        dedup = MagicMock()
        dedup.is_new.return_value = True
        return fenwick, bucket, ewma, price, dedup

    def test_empty_batch(self) -> None:
        fenwick, bucket, ewma, price, dedup = self._make_fakes()
        result = process_batch([], fenwick, bucket, ewma, price, dedup)
        assert result.processed_count == 0
        assert result.mismatch_count == 0

    def test_batch_of_3(self) -> None:
        fenwick, bucket, ewma, price, dedup = self._make_fakes()
        spans = [_make_span(span_id=f"s-{i}") for i in range(3)]
        result = process_batch(spans, fenwick, bucket, ewma, price, dedup)
        assert result.processed_count == 3
        assert fenwick.pipeline_update.call_count == 3

    def test_batch_counts_mismatches(self) -> None:
        fenwick, bucket, ewma, price, dedup = self._make_fakes()
        spans = [
            _make_span(span_id="s-0", cost_usd_micro=1500),
            _make_span(span_id="s-1", cost_usd_micro=9999),
            _make_span(span_id="s-2", cost_usd_micro=9999),
        ]
        result = process_batch(spans, fenwick, bucket, ewma, price, dedup)
        assert result.processed_count == 3
        assert result.mismatch_count == 2

    def test_all_duplicates_skipped(self) -> None:
        fenwick, bucket, ewma, price, dedup = self._make_fakes()
        dedup.is_new.return_value = False
        spans = [_make_span(span_id=f"s-{i}") for i in range(5)]
        result = process_batch(spans, fenwick, bucket, ewma, price, dedup)
        assert result.processed_count == 5
        fenwick.pipeline_update.assert_not_called()


class TestRetryUtility:
    def test_succeeds_on_first_try(self) -> None:
        from shared.utils.retry import with_retry
        fn = MagicMock(return_value=42)
        assert with_retry(fn) == 42
        fn.assert_called_once()

    def test_succeeds_on_second_try(self) -> None:
        from shared.utils.retry import with_retry
        fn = MagicMock(side_effect=[RuntimeError("fail"), 42])
        assert with_retry(fn, max_retries=3, base_ms=1) == 42
        assert fn.call_count == 2

    def test_raises_after_max_retries(self) -> None:
        from shared.utils.retry import with_retry
        from shared.types.cost_types import ProcessingError
        fn = MagicMock(side_effect=RuntimeError("always fail"))
        with pytest.raises(ProcessingError, match="Failed after 3 retries"):
            with_retry(fn, max_retries=3, base_ms=1)
        assert fn.call_count == 3

    def test_exponential_backoff_timing(self) -> None:
        from shared.utils.retry import with_retry
        from shared.types.cost_types import ProcessingError
        fn = MagicMock(side_effect=RuntimeError("fail"))
        start = time.monotonic()
        with pytest.raises(ProcessingError):
            with_retry(fn, max_retries=3, base_ms=50)
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms >= 300


class TestConfigLoading:
    def test_defaults(self) -> None:
        from worker.config import load_config
        config = load_config(env={})
        assert config.kafka_bootstrap_servers == "localhost:9092"
        assert config.kafka_consumer_group == "event-cost-worker-group"
        assert config.kafka_topic == "llm.spans.raw"
        assert config.kafka_dlq_topic == "llm.spans.raw.dlq"
        assert config.batch_size == 500
        assert config.max_retries == 3
        assert config.retry_base_ms == 100

    def test_overrides(self) -> None:
        from worker.config import load_config
        config = load_config(env={
            "KAFKA_BOOTSTRAP_SERVERS": "broker:9093",
            "BATCH_SIZE": "100",
            "MAX_RETRIES": "5",
        })
        assert config.kafka_bootstrap_servers == "broker:9093"
        assert config.batch_size == 100
        assert config.max_retries == 5


class TestContractValidator:
    def test_loads_valid_contract(self) -> None:
        from shared.contracts.validator import load_event_contract
        result = load_event_contract()
        assert result["event"] == "llm_spans_raw"
        assert result["version"] == 1
        assert result["consumer_group"] == "event-cost-worker-group"

    def test_missing_contract_raises(self) -> None:
        from shared.contracts.validator import load_event_contract
        import shared.contracts.validator as v
        original = v.CONTRACT_FILE
        try:
            from pathlib import Path
            v.CONTRACT_FILE = Path("/nonexistent/contract.yaml")
            with pytest.raises(ValueError, match="Contract file not found"):
                load_event_contract()
        finally:
            v.CONTRACT_FILE = original


class TestRawSpanEventFrozen:
    def test_immutable(self) -> None:
        span = _make_span()
        with pytest.raises(AttributeError):
            span.span_id = "new-id"

    def test_raw_bytes_excluded_from_repr(self) -> None:
        span = _make_span(raw_bytes=b"x" * 10000)
        r = repr(span)
        assert "xxxx" not in r
