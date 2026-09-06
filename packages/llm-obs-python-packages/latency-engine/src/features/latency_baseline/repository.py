from __future__ import annotations

from typing import Any
from shared.ports.clickhouse_port import ClickHousePort, BaselinePoint


class LatencyBaselineRepository:
    def __init__(self, clickhouse: ClickHousePort) -> None:
        self._clickhouse = clickhouse

    def get_baseline(self, model: str, hour_of_day: int, days: int) -> list[BaselinePoint]:
        return self._clickhouse.get_baseline(model, hour_of_day, days)
