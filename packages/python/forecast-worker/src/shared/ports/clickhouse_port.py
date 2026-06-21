from typing import Protocol, List, Tuple
from datetime import datetime


class ClickHousePort(Protocol):
    def fetch_cost_series_raw(
        self, lookback_hours: int
    ) -> List[Tuple[str, str, datetime, float]]:
        """
        Fetch raw cost series aggregated by service, model, and hour bucket from ClickHouse.
        """
        ...
