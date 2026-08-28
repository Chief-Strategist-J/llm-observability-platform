from typing import List, Tuple
from datetime import date, datetime
import clickhouse_connect
from shared.ports.clickhouse_port import ClickHousePort
from shared.tracing.tracer import trace_span

class ClickHouseAdapter(ClickHousePort):
    def __init__(self, host: str, port: int, username: str, password: str, database: str):
        self.client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
        )

    def insert_latency_checkpoints(self, rows: list[tuple]) -> None:
        if not rows:
            return
        column_names = [
            "model", "endpoint", "checkpoint_date", "hour_of_day",
            "p50_ttft_ms", "p95_ttft_ms", "p99_ttft_ms",
            "p50_total_ms", "p95_total_ms", "p99_total_ms",
            "sample_count", "slo_violation_count", "timestamp"
        ]
        data = [list(row) for row in rows]
        with trace_span(
            "clickhouse:insert_latency_checkpoints",
            attributes={
                "db.system": "clickhouse",
                "row_count": len(rows)
            }
        ):
            self.client.insert("latency_checkpoints", data, column_names=column_names)

    def get_p99_ttft_history_7d(self, model: str, endpoint: str, hour_of_day: int) -> list[float]:
        with trace_span(
            "clickhouse:get_p99_ttft_history_7d",
            attributes={
                "db.system": "clickhouse",
                "model": model,
                "endpoint": endpoint,
                "hour_of_day": hour_of_day
            }
        ):
            query = """
            SELECT p99_ttft_ms
            FROM latency_checkpoints
            WHERE model = %(model)s
              AND endpoint = %(endpoint)s
              AND hour_of_day = %(hour_of_day)s
              AND timestamp >= now() - INTERVAL 7 DAY
            ORDER BY timestamp DESC
            """
            result = self.client.query(query, {
                "model": model,
                "endpoint": endpoint,
                "hour_of_day": hour_of_day
            })
            return [float(row[0]) for row in result.result_rows if row[0] is not None]
