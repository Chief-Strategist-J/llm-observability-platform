import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from shared.ports.timesfm_port import TimesFMPort
from features.forecast.repository import ForecastRepository

logger = logging.getLogger(__name__)


class ForecastService:
    @staticmethod
    def build_dense_series(
        raw_rows: List[Tuple[str, str, datetime, float]],
        lookback_hours: int = 168,
        min_history_hours: int = 48,
        anchor_time: datetime | None = None,
    ) -> Tuple[Dict[Tuple[str, str], List[float]], List[Tuple[str, str]]]:
        """
        Processes raw query rows and builds dense hourly series for each (service, model) pair.
        Pads missing hours with 0. Excludes pairs with fewer than min_history_hours data points.

        Returns:
            dense_series: Dict[(service, model)] -> List[float] (length = lookback_hours)
            skip_list: List[Tuple[str, str]] (pairs that were excluded)
        """
        if anchor_time is None:
            # Anchor to the current hour start
            now = datetime.utcnow()
            anchor_time = now.replace(minute=0, second=0, microsecond=0)

        # Generate the dense hour buckets (chronological order)
        # Bins run from (anchor_time - lookback_hours + 1) to anchor_time
        start_time = anchor_time - timedelta(hours=lookback_hours - 1)
        hour_buckets = [start_time + timedelta(hours=i) for i in range(lookback_hours)]
        bucket_to_index = {bucket: i for i, bucket in enumerate(hour_buckets)}

        # Group raw data by (service, model)
        grouped_raw: Dict[Tuple[str, str], Dict[datetime, float]] = {}
        for service, model, hour_bucket, total_cost in raw_rows:
            pair = (service, model)
            # Normalize hour_bucket to start of hour
            normalized_bucket = hour_bucket.replace(minute=0, second=0, microsecond=0)
            if pair not in grouped_raw:
                grouped_raw[pair] = {}
            grouped_raw[pair][normalized_bucket] = total_cost

        dense_series: Dict[Tuple[str, str], List[float]] = {}
        skip_list: List[Tuple[str, str]] = []

        for pair, history in grouped_raw.items():
            service, model = pair
            # An actual data point is a recorded hour bucket in the database
            # count the number of history points falling in our lookback window
            points_in_window = 0
            series_values = [0.0] * lookback_hours

            for bucket, value in history.items():
                if bucket in bucket_to_index:
                    points_in_window += 1
                    idx = bucket_to_index[bucket]
                    series_values[idx] = value

            if points_in_window < min_history_hours:
                # Log metric for insufficient history
                logger.info(
                    "forecast_skipped_insufficient_history_total service=%s model=%s history_points=%d minimum=%d",
                    service,
                    model,
                    points_in_window,
                    min_history_hours,
                )
                skip_list.append(pair)
            else:
                dense_series[pair] = series_values

        return dense_series, skip_list

    @staticmethod
    def generate_forecast_fallback(series: list[float], horizon: int = 24) -> tuple[list[float], list[float], list[float]]:
        if not series:
            series = [0.0]
        avg = sum(series) / len(series)
        mean = [avg] * horizon
        p10 = [val * 0.8 for val in mean]
        p90 = [val * 1.2 for val in mean]
        return mean, p10, p90

    @classmethod
    def get_forecast(
        cls,
        service: str,
        model: str,
        forecast_type: str,  # "cost" or "latency"
        repo: ForecastRepository,
        timesfm_port: Optional[TimesFMPort] = None
    ) -> Tuple[dict, str]:
        # 1. Try Redis lookup
        cached = repo.fetch_from_redis(service, model)
        if cached:
            return cached, "redis"

        # 2. ClickHouse fallback
        if forecast_type == "cost":
            raw_rows = repo.fetch_cost_series_raw(168)
        else:
            raw_rows = repo.fetch_latency_series_raw(168)

        dense, _ = cls.build_dense_series(
            raw_rows,
            lookback_hours=168,
            min_history_hours=1,  # allow fallback even with minimal history
        )
        pair_key = (service, model)
        if pair_key not in dense:
            raise ValueError(f"No historical {forecast_type} data found to build forecast")

        series = dense[pair_key]
        if timesfm_port:
            try:
                mean_list, p10_list, p90_list = timesfm_port.forecast(series, horizon=24)
            except Exception:
                mean_list, p10_list, p90_list = cls.generate_forecast_fallback(series, horizon=24)
        else:
            mean_list, p10_list, p90_list = cls.generate_forecast_fallback(series, horizon=24)

        forecast_time = datetime.utcnow()
        mean_val = mean_list[-1]
        p10_val = p10_list[-1]
        p90_val = p90_list[-1]

        # Cache back to Redis
        repo.cache_in_redis(service, model, forecast_time, mean_val, p10_val, p90_val)

        return {
            "mean": mean_val,
            "p10": p10_val,
            "p90": p90_val,
            "timestamp": forecast_time.isoformat()
        }, "clickhouse"

    @classmethod
    def calculate_breach_risk(
        cls,
        service: str,
        model: str,
        p90_val: float,
        repo: ForecastRepository
    ) -> dict:
        budget_limit = repo.get_budget_limit_for_service_model(service, model)
        p90_usd = p90_val / 1_000_000.0
        breach_predicted = False
        if budget_limit is not None:
            breach_predicted = p90_usd > budget_limit
        return {
            "budget_limit": budget_limit,
            "predicted_cost_p90_usd": p90_usd,
            "breach_predicted": breach_predicted
        }

    @classmethod
    def get_forecasts_summary(cls, repo: ForecastRepository) -> List[dict]:
        all_forecasts = repo.get_all_forecasts()
        budgets = repo.get_budget_limits()
        
        budget_map = {}
        for u_id, m, max_budget in budgets:
            budget_map[(u_id, m)] = max_budget
            
        summary_list = []
        for service, model, f_time, mean, p10, p90 in all_forecasts:
            f_time_str = f_time.isoformat() if isinstance(f_time, datetime) else str(f_time)
            limit = budget_map.get((service, model))
            
            p90_usd = p90 / 1_000_000.0
            breach_predicted = False
            if limit is not None:
                breach_predicted = p90_usd > limit
                
            summary_list.append({
                "service": service,
                "model": model,
                "forecast_time": f_time_str,
                "mean": mean,
                "p10": p10,
                "p90": p90,
                "budget_limit": limit,
                "breach_predicted": breach_predicted
            })
        return summary_list

