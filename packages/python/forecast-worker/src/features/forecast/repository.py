from datetime import datetime
from typing import List, Tuple, Optional
import json
from shared.ports.redis_port import RedisPort
from shared.ports.clickhouse_port import ClickHousePort
from shared.ports.postgres_port import PostgresPort

class ForecastRepository:
    def __init__(
        self,
        redis_port: RedisPort,
        clickhouse_port: ClickHousePort,
        postgres_port: PostgresPort
    ):
        self.redis_port = redis_port
        self.clickhouse_port = clickhouse_port
        self.postgres_port = postgres_port

    def fetch_from_redis(self, service: str, model: str) -> Optional[dict]:
        try:
            # Check :latest key first
            latest_key = f"forecast:{service}:{model}:latest"
            val = self.redis_port.client.get(latest_key)
            if val:
                return json.loads(val)
            
            # Fall back to scanning keys
            pattern = f"forecast:{service}:{model}:*"
            keys = self.redis_port.client.keys(pattern)
            if not keys:
                return None
            
            keys_str = [k.decode("utf-8") if isinstance(k, bytes) else k for k in keys]
            valid_keys = [k for k in keys_str if not k.endswith(":latest")]
            if not valid_keys:
                return None
            
            valid_keys.sort()
            val = self.redis_port.client.get(valid_keys[-1])
            if val:
                return json.loads(val)
        except Exception:
            pass
        return None

    def cache_in_redis(
        self,
        service: str,
        model: str,
        forecast_time: datetime,
        mean_val: float,
        p10_val: float,
        p90_val: float
    ) -> None:
        self.redis_port.cache_forecast(service, model, forecast_time, mean_val, p10_val, p90_val)
        latest_key = f"forecast:{service}:{model}:latest"
        latest_data = {
            "mean": mean_val,
            "p10": p10_val,
            "p90": p90_val,
            "timestamp": forecast_time.isoformat()
        }
        try:
            self.redis_port.client.setex(latest_key, 3600, json.dumps(latest_data))
        except Exception:
            pass

    def fetch_cost_series_raw(self, lookback_hours: int) -> List[Tuple[str, str, datetime, float]]:
        return self.clickhouse_port.fetch_cost_series_raw(lookback_hours)

    def fetch_latency_series_raw(self, lookback_hours: int) -> List[Tuple[str, str, datetime, float]]:
        return self.clickhouse_port.fetch_latency_series_raw(lookback_hours)

    def get_budget_limits(self) -> List[Tuple[str, str, float]]:
        return self.postgres_port.get_budget_limits()

    def get_all_forecasts(self) -> List[Tuple[str, str, datetime, float, float, float]]:
        return self.postgres_port.get_all_forecasts()
