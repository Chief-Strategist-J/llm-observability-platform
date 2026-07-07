from typing import Protocol, List, Tuple, Optional
from datetime import datetime

class PostgresPort(Protocol):
    def write_forecast(
        self,
        service: str,
        model: str,
        forecast_time: datetime,
        mean: float,
        p10: float,
        p90: float
    ) -> None:
        """
        Write or upsert forecast values into Postgres forecasts table.
        """
        ...

    def get_budget_limits(self) -> List[Tuple[str, str, float]]:
        """
        Fetch budget configs (user_id/service, model, max_budget) from the database.
        """
        ...
