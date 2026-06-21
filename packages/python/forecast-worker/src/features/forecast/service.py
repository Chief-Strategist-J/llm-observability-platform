import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set

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
