from typing import Protocol, List, Tuple
from datetime import date

class ClickHousePort(Protocol):
    def insert_quality_trends(self, rows: List[Tuple[date, str, str, str, float, int, int]]) -> None: ...
