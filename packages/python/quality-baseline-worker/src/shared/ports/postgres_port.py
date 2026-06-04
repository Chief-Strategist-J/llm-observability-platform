from typing import Protocol, List
from datetime import datetime
from features.quality_baseline.types import BaselineRecomputeResult, DailyRollupRecord

class PostgresPort(Protocol):
    def get_rolling_baselines(self) -> List[BaselineRecomputeResult]: ...
    def get_daily_rollup_data(self, start_time: datetime, end_time: datetime) -> List[DailyRollupRecord]: ...
