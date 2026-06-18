import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from worker.activities import SloBurnActivities

@pytest.fixture(autouse=True)
def mock_activity_info(monkeypatch):
    class MockInfo:
        workflow_id = "test-workflow"
        workflow_run_id = "test-run"
    monkeypatch.setattr("temporalio.activity.info", lambda: MockInfo())

@pytest.mark.asyncio
async def test_fetch_active_pairs():
    redis = MagicMock()
    redis.scan_slo_keys.return_value = [("gpt-4o", "/v1/chat/completions")]
    clickhouse = MagicMock()
    kafka = MagicMock()
    metrics = MagicMock()

    activities = SloBurnActivities(
        redis=redis,
        clickhouse=clickhouse,
        kafka=kafka,
        metrics=metrics,
        slo_compliance_config_path="nonexistent.yaml",
        default_slo_compliance=0.95
    )

    pairs = await activities.fetch_active_pairs()
    assert pairs == [("gpt-4o", "/v1/chat/completions")]
    redis.scan_slo_keys.assert_called_once()

@pytest.mark.asyncio
async def test_compute_burn_rates():
    redis = MagicMock()
    # Mock get_slo_buckets to return 5 errors and 100 requests for any call
    def mock_get_slo_buckets(model, endpoint, buckets):
        n = len(buckets)
        return ([1] * n, [20] * n)
    redis.get_slo_buckets.side_effect = mock_get_slo_buckets

    clickhouse = MagicMock()
    kafka = MagicMock()
    metrics = MagicMock()

    activities = SloBurnActivities(
        redis=redis,
        clickhouse=clickhouse,
        kafka=kafka,
        metrics=metrics,
        slo_compliance_config_path="nonexistent.yaml",
        default_slo_compliance=0.95
    )

    # 1/20 = 0.05 error rate. slo_threshold = 0.95. EB = 0.05. Burn rate = 0.05/0.05 = 1.0.
    res = await activities.compute_burn_rates("gpt-4o", "/v1/chat/completions", 1700000000)
    assert res["fast"] == pytest.approx(1.0)
    assert res["medium"] == pytest.approx(1.0)
    assert res["slow"] == pytest.approx(1.0)

@pytest.mark.asyncio
async def test_write_burn_rates():
    redis = MagicMock()
    clickhouse = MagicMock()
    kafka = MagicMock()
    metrics = MagicMock()

    activities = SloBurnActivities(
        redis=redis,
        clickhouse=clickhouse,
        kafka=kafka,
        metrics=metrics,
        slo_compliance_config_path="nonexistent.yaml",
        default_slo_compliance=0.95
    )

    rates = {"fast": 1.5, "medium": 1.0, "slow": 0.5}
    await activities.write_burn_rates("gpt-4o", "/v1/chat/completions", rates)
    
    redis.write_burn_rate.assert_any_call("fast", "gpt-4o", "/v1/chat/completions", 1.5, 300)
    redis.write_burn_rate.assert_any_call("medium", "gpt-4o", "/v1/chat/completions", 1.0, 7200)
    redis.write_burn_rate.assert_any_call("slow", "gpt-4o", "/v1/chat/completions", 0.5, 86400)

@pytest.mark.asyncio
async def test_handle_alerts_no_severity():
    redis = MagicMock()
    clickhouse = MagicMock()
    kafka = MagicMock()
    metrics = MagicMock()

    activities = SloBurnActivities(
        redis=redis,
        clickhouse=clickhouse,
        kafka=kafka,
        metrics=metrics,
        slo_compliance_config_path="nonexistent.yaml",
        default_slo_compliance=0.95
    )

    # All burn rates low -> no alert severity
    rates = {"fast": 0.1, "medium": 0.1, "slow": 0.1}
    await activities.handle_alerts("gpt-4o", "/v1/chat/completions", rates, 1700000000)
    redis.check_and_set_dedup_lock.assert_not_called()

@pytest.mark.asyncio
async def test_handle_alerts_page_lock_failed():
    redis = MagicMock()
    redis.check_and_set_dedup_lock.return_value = False
    clickhouse = MagicMock()
    kafka = MagicMock()
    metrics = MagicMock()

    activities = SloBurnActivities(
        redis=redis,
        clickhouse=clickhouse,
        kafka=kafka,
        metrics=metrics,
        slo_compliance_config_path="nonexistent.yaml",
        default_slo_compliance=0.95
    )

    # Page alert: fast > 14.4, medium > 6.0
    rates = {"fast": 15.0, "medium": 7.0, "slow": 4.0}
    await activities.handle_alerts("gpt-4o", "/v1/chat/completions", rates, 1700000000)
    redis.check_and_set_dedup_lock.assert_called_once_with("gpt-4o", "/v1/chat/completions", "page", 900)
    metrics.record_alert_deduped.assert_called_once_with("gpt-4o", "/v1/chat/completions", "page")
    kafka.publish_alert.assert_not_called()

@pytest.mark.asyncio
async def test_handle_alerts_success():
    redis = MagicMock()
    redis.check_and_set_dedup_lock.return_value = True
    redis.get_ddsketch_percentiles.return_value = (180.0, 250.0)
    
    # get_slo_buckets for 43200 total buckets
    def mock_get_slo_buckets(model, endpoint, buckets):
        n = len(buckets)
        return ([0] * n, [10] * n)
    redis.get_slo_buckets.side_effect = mock_get_slo_buckets

    clickhouse = MagicMock()
    clickhouse.get_baseline_p95_7d.return_value = 175.0
    
    kafka = MagicMock()
    metrics = MagicMock()

    activities = SloBurnActivities(
        redis=redis,
        clickhouse=clickhouse,
        kafka=kafka,
        metrics=metrics,
        slo_compliance_config_path="nonexistent.yaml",
        default_slo_compliance=0.95
    )

    rates = {"fast": 15.0, "medium": 7.0, "slow": 4.0}
    await activities.handle_alerts("gpt-4o", "/v1/chat/completions", rates, 1700000000)
    
    redis.check_and_set_dedup_lock.assert_called_once_with("gpt-4o", "/v1/chat/completions", "page", 900)
    redis.get_ddsketch_percentiles.assert_called_once()
    clickhouse.get_baseline_p95_7d.assert_called_once_with("gpt-4o", "/v1/chat/completions")
    redis.write_budget_remaining.assert_called_once()
    kafka.publish_alert.assert_called_once()
    metrics.record_alert_sent.assert_called_once_with("gpt-4o", "/v1/chat/completions", "page")
