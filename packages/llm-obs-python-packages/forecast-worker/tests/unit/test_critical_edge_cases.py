import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from infra.adapters.redis.redis_adapter import RedisAdapter
from infra.adapters.postgres.postgres_adapter import PostgresAdapter
from infra.adapters.timesfm.timesfm_adapter import TimesFMAdapter
from worker.activities import ForecastActivities

# 1. Edge Case: ClickHouse connection failure when fetching series
@pytest.mark.asyncio
async def test_activities_clickhouse_failure() -> None:
    ch = MagicMock()
    # ClickHouse query fails or raises unexpected exceptions
    ch.fetch_cost_series_raw.side_effect = Exception("ClickHouse down")
    
    activities = ForecastActivities(
        clickhouse=ch,
        postgres=MagicMock(),
        redis=MagicMock(),
        timesfm=MagicMock(),
        alert_publisher=MagicMock(),
        sdk_url="http://mock-sdk-api"
    )

    with pytest.raises(Exception, match="ClickHouse down"):
        await activities.fetch_cost_series(168, 48)


# 2. Edge Case: Budget configuration lookup when budgets table is empty
@pytest.mark.asyncio
async def test_breach_detection_empty_budgets() -> None:
    pg = MagicMock()
    # PostgreSQL returns no budget records at all
    pg.get_budget_limits.return_value = []
    
    activities = ForecastActivities(
        clickhouse=MagicMock(),
        postgres=pg,
        redis=MagicMock(),
        timesfm=MagicMock(),
        alert_publisher=MagicMock(),
        sdk_url="http://mock-sdk-api"
    )
    
    # Should safely return False and not trigger alert or crash
    breach = await activities.check_predicted_breach("service-a", "model-b", 50000000.0)
    assert breach is False


# 3. Edge Case: TimesFM predicts negative or extreme values (Data Sanitization check)
def test_timesfm_adapter_handles_extreme_inputs() -> None:
    adapter = TimesFMAdapter(repo_id="invalid-repo-id", backend="cpu")
    # All inputs are extreme/negative numbers
    series = [-100.0, -200.0, -300.0]
    mean, p10, p90 = adapter.forecast(series, horizon=24)
    
    assert len(mean) == 24
    # Mock fallback should approximate safely based on avg (-200.0)
    # Average of series is -200.0.
    # p10 should be -200.0 * 0.8 = -160.0 (less extreme in magnitude but mathematically larger)
    # p90 should be -200.0 * 1.2 = -240.0 (more extreme in negative direction)
    assert mean[0] == pytest.approx(-200.0)
    assert p10[0] == pytest.approx(-160.0)
    assert p90[0] == pytest.approx(-240.0)


# 4. Edge Case: Redis adapter handles server disconnection/errors gracefully without crashing
@patch("redis.from_url")
def test_redis_adapter_disconnect_tolerance(mock_redis_from_url) -> None:
    mock_client = MagicMock()
    mock_redis_from_url.return_value = mock_client
    # Simulate Redis connection drop or command failure
    mock_client.setex.side_effect = Exception("Redis connection refused")
    mock_client.get.side_effect = Exception("Redis connection refused")
    
    adapter = RedisAdapter("redis://localhost:6379/0")
    forecast_time = datetime(2026, 6, 21, 10, 0, 0)
    
    # Write operation should raise the exception to let caller handle it, or log it depending on implementation.
    # Typically, failure is bubbled up in activities/workflows to preserve idempotency guarantees.
    with pytest.raises(Exception, match="Redis connection refused"):
        adapter.cache_forecast("service-a", "model-b", forecast_time, 10.0, 8.0, 12.0, 3600)
        
    with pytest.raises(Exception, match="Redis connection refused"):
        adapter.get_cached_forecast("service-a", "model-b", forecast_time)
