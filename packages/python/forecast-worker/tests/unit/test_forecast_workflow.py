import pytest
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock
from temporalio import activity
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment
from worker.workflows import ForecastWorkflow, ForecastWorkflowInput
from worker.activities import ForecastActivities

# Mocks for activities testing
class MockClickHousePort:
    def fetch_cost_series_raw(self, lookback_hours):
        # Return 50 data points to satisfy the min_history_hours=48 requirement
        anchor = datetime.utcnow()
        return [("service-a", "model-b", anchor - timedelta(hours=i), 10.0 + i) for i in range(50)]

    def fetch_latency_series_raw(self, lookback_hours):
        anchor = datetime.utcnow()
        return [("service-a", "model-b", anchor - timedelta(hours=i), 50.0 + i) for i in range(50)]

class MockPostgresPort:
    def __init__(self):
        self.write_calls = []
        self.budgets = [("service-a", "model-b", 10.0)] # $10 max budget

    def write_forecast(self, service, model, forecast_time, mean, p10, p90):
        self.write_calls.append((service, model, forecast_time, mean, p10, p90))

    def get_budget_limits(self):
        return self.budgets

class MockRedisPort:
    def __init__(self):
        self.cache = {}

    def cache_forecast(self, service, model, forecast_time, mean, p10, p90, ttl_seconds=3600):
        key = f"{service}:{model}:{forecast_time.isoformat()}"
        self.cache[key] = {"mean": mean, "p10": p10, "p90": p90}

    def get_cached_forecast(self, service, model, forecast_time):
        key = f"{service}:{model}:{forecast_time.isoformat()}"
        return self.cache.get(key)

class MockTimesFMPort:
    def forecast(self, series, horizon=24):
        return [1.0] * horizon, [0.8] * horizon, [1.2] * horizon

class MockAlertPublisherPort:
    def __init__(self):
        self.breaches = []

    def publish_predicted_breach(self, payload):
        self.breaches.append(payload)


@pytest.mark.asyncio
async def test_forecast_activities() -> None:
    ch = MockClickHousePort()
    pg = MockPostgresPort()
    redis = MockRedisPort()
    timesfm = MockTimesFMPort()
    alert_pub = MockAlertPublisherPort()

    activities = ForecastActivities(
        clickhouse=ch,
        postgres=pg,
        redis=redis,
        timesfm=timesfm,
        alert_publisher=alert_pub,
        sdk_url="http://mock-sdk-api"
    )

    # 1. Test fetch_cost_series
    cost_res = await activities.fetch_cost_series(168, 48)
    assert "dense" in cost_res
    assert "service-a||model-b" in cost_res["dense"]
    assert len(cost_res["dense"]["service-a||model-b"]) == 168

    # 2. Test fetch_latency_series
    latency_res = await activities.fetch_latency_series(168, 48)
    assert "dense" in latency_res
    assert "service-a||model-b" in latency_res["dense"]

    # 3. Test run_timesfm_forecast
    forecast_res = await activities.run_timesfm_forecast([1.0] * 168, 24)
    assert len(forecast_res["mean"]) == 24
    assert len(forecast_res["p10"]) == 24
    assert len(forecast_res["p90"]) == 24

    # 4. Test write_forecast_outputs
    forecast_time = datetime(2026, 6, 21, 10, 0, 0)
    await activities.write_forecast_outputs(
        "service-a", "model-b", forecast_time.isoformat(), 15.0, 12.0, 18.0
    )
    assert len(pg.write_calls) == 1
    assert pg.write_calls[0] == ("service-a", "model-b", forecast_time, 15.0, 12.0, 18.0)

    # 5. Test check_predicted_breach
    # Budget is $10.0 (10,000,000 micro-USD).
    # Test no breach: p90 is 5,000,000 micro-USD ($5.0)
    breach = await activities.check_predicted_breach("service-a", "model-b", 5_000_000.0)
    assert breach is False
    assert len(alert_pub.breaches) == 0

    # Test breach: p90 is 12,000,000 micro-USD ($12.0)
    breach = await activities.check_predicted_breach("service-a", "model-b", 12_000_000.0)
    assert breach is True
    assert len(alert_pub.breaches) == 1
    assert alert_pub.breaches[0]["predicted_p90_usd"] == 12.0


# Mock activities for workflow execution
@activity.defn(name="fetch_cost_series")
async def mock_wf_fetch_cost_series(lookback_hours: int, min_history_hours: int) -> dict:
    return {
        "dense": {"service-a||model-b": [10.0] * 168},
        "skip": []
    }

@activity.defn(name="fetch_latency_series")
async def mock_wf_fetch_latency_series(lookback_hours: int, min_history_hours: int) -> dict:
    return {
        "dense": {"service-a||model-b": [50.0] * 168},
        "skip": []
    }

@activity.defn(name="run_timesfm_forecast")
async def mock_wf_run_timesfm_forecast(series: list[float], horizon: int = 24) -> dict:
    # return values such that last value of p90 is 15,000,000 micro-USD ($15.0) which breaches $10 limit
    return {
        "mean": [12_000_000.0] * horizon,
        "p10": [9_000_000.0] * horizon,
        "p90": [15_000_000.0] * horizon,
    }

write_forecast_calls = []
@activity.defn(name="write_forecast_outputs")
async def mock_wf_write_forecast_outputs(
    service: str, model: str, forecast_time_iso: str, mean: float, p10: float, p90: float
) -> None:
    write_forecast_calls.append((service, model, mean, p10, p90))

check_breach_calls = []
@activity.defn(name="check_predicted_breach")
async def mock_wf_check_predicted_breach(service: str, model: str, p90_val: float) -> bool:
    check_breach_calls.append((service, model, p90_val))
    return True


@pytest.mark.asyncio
async def test_forecast_workflow() -> None:
    global write_forecast_calls, check_breach_calls
    write_forecast_calls = []
    check_breach_calls = []

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="forecast-test-queue",
            workflows=[ForecastWorkflow],
            activities=[
                mock_wf_fetch_cost_series,
                mock_wf_fetch_latency_series,
                mock_wf_run_timesfm_forecast,
                mock_wf_write_forecast_outputs,
                mock_wf_check_predicted_breach,
            ],
        ):
            await env.client.execute_workflow(
                ForecastWorkflow.run,
                ForecastWorkflowInput(lookback_hours=168, min_history_hours=48),
                id="test-forecast-wf",
                task_queue="forecast-test-queue",
            )

    assert len(write_forecast_calls) == 1
    assert write_forecast_calls[0] == ("service-a", "model-b", 12_000_000.0, 9_000_000.0, 15_000_000.0)
    assert len(check_breach_calls) == 1
    assert check_breach_calls[0] == ("service-a", "model-b", 15_000_000.0)
