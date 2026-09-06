import logging
import httpx
from datetime import datetime
from temporalio import activity
from features.forecast.service import ForecastService
from shared.ports.clickhouse_port import ClickHousePort
from shared.ports.postgres_port import PostgresPort
from shared.ports.redis_port import RedisPort
from shared.ports.timesfm_port import TimesFMPort
from shared.ports.alert_publisher_port import AlertPublisherPort

logger = logging.getLogger(__name__)

class ForecastActivities:
    def __init__(
        self,
        clickhouse: ClickHousePort,
        postgres: PostgresPort,
        redis: RedisPort,
        timesfm: TimesFMPort,
        alert_publisher: AlertPublisherPort,
        sdk_url: str,
    ):
        self.clickhouse = clickhouse
        self.postgres = postgres
        self.redis = redis
        self.timesfm = timesfm
        self.alert_publisher = alert_publisher
        self.sdk_url = sdk_url

    @activity.defn(name="fetch_cost_series")
    async def fetch_cost_series(self, lookback_hours: int, min_history_hours: int) -> dict:
        raw_rows = self.clickhouse.fetch_cost_series_raw(lookback_hours)
        dense, skip = ForecastService.build_dense_series(
            raw_rows,
            lookback_hours=lookback_hours,
            min_history_hours=min_history_hours,
        )
        return {
            "dense": {f"{k[0]}||{k[1]}": v for k, v in dense.items()},
            "skip": [list(x) for x in skip]
        }

    @activity.defn(name="fetch_latency_series")
    async def fetch_latency_series(self, lookback_hours: int, min_history_hours: int) -> dict:
        raw_rows = self.clickhouse.fetch_latency_series_raw(lookback_hours)
        dense, skip = ForecastService.build_dense_series(
            raw_rows,
            lookback_hours=lookback_hours,
            min_history_hours=min_history_hours,
        )
        return {
            "dense": {f"{k[0]}||{k[1]}": v for k, v in dense.items()},
            "skip": [list(x) for x in skip]
        }

    @activity.defn(name="run_timesfm_forecast")
    async def run_timesfm_forecast(self, series: list[float], horizon: int = 24) -> dict:
        mean, p10, p90 = self.timesfm.forecast(series, horizon=horizon)
        return {
            "mean": mean,
            "p10": p10,
            "p90": p90
        }

    @activity.defn(name="write_forecast_outputs")
    async def write_forecast_outputs(
        self,
        service: str,
        model: str,
        forecast_time_iso: str,
        mean: float,
        p10: float,
        p90: float
    ) -> None:
        forecast_time = datetime.fromisoformat(forecast_time_iso)
        self.postgres.write_forecast(service, model, forecast_time, mean, p10, p90)
        self.redis.cache_forecast(service, model, forecast_time, mean, p10, p90)
        
        url = f"{self.sdk_url.rstrip('/')}/v1/metrics/forecast"
        payload = {
            "mean": int(mean),
            "p10": int(p10),
            "p90": int(p90),
            "model": model,
            "provider": "unknown",
            "service_name": service
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=5.0)
                resp.raise_for_status()
        except Exception as e:
            logger.warning("Failed to push forecast to SDK API: %s", e)

    @activity.defn(name="check_predicted_breach")
    async def check_predicted_breach(
        self,
        service: str,
        model: str,
        p90_forecast_val: float
    ) -> bool:
        budgets = self.postgres.get_budget_limits()
        matched_budget = None
        for u_id, m, max_budget in budgets:
            if u_id == service and m == model:
                matched_budget = max_budget
                break
        
        if matched_budget is not None:
            p90_usd = p90_forecast_val / 1_000_000.0
            if p90_usd > matched_budget:
                payload = {
                    "service": service,
                    "model": model,
                    "max_budget": matched_budget,
                    "predicted_p90_usd": p90_usd,
                    "event_type": "predicted_breach",
                    "timestamp_utc": datetime.utcnow().isoformat() + "Z"
                }
                self.alert_publisher.publish_predicted_breach(payload)
                return True
        return False
