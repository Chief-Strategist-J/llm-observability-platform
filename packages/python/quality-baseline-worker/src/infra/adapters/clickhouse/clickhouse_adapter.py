from typing import List, Tuple
from datetime import date
import clickhouse_connect
from shared.ports.clickhouse_port import ClickHousePort

class ClickHouseAdapter(ClickHousePort):
    def __init__(self, host: str, port: int, username: str, password: str, database: str):
        self.client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
        )

    def insert_quality_trends(self, rows: List[Tuple[date, str, str, str, float, int, int]]) -> None:
        if not rows:
            return
        column_names = [
            "rollup_date", "model", "endpoint", "prompt_type", 
            "avg_composite_score", "flag_count", "sample_count"
        ]
        data = [list(row) for row in rows]
        self.client.insert("quality_trend", data, column_names=column_names)
