from typing import List, Tuple
from datetime import date, datetime
import clickhouse_connect
from shared.ports.clickhouse_port import ClickHousePort
from shared.tracing.tracer import trace_span
from infra.adapters.clickhouse.models import LatencyCheckpointModel
from infra.adapters.clickhouse.queries import ClickHouseQueryRegistry

class ClickHouseAdapter(ClickHousePort):
    def __init__(self, host: str, port: int, username: str, password: str, database: str):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._database = database
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                database=self._database,
            )
        return self._client

    def insert_latency_checkpoints(self, rows: list[tuple]) -> None:
        if not rows:
            return
        column_names = LatencyCheckpointModel.column_names()
        table_name = LatencyCheckpointModel.table_name()
        data = [list(row) for row in rows]
        with trace_span(
            "clickhouse:insert_latency_checkpoints",
            attributes={
                "db.system": "clickhouse",
                "row_count": len(rows)
            }
        ):
            self.client.insert(table_name, data, column_names=column_names)

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
            query = ClickHouseQueryRegistry.P99_TTFT_HISTORY_QUERY
            result = self.client.query(query, {
                "model": model,
                "endpoint": endpoint,
                "hour_of_day": hour_of_day
            })
            return [float(row[0]) for row in result.result_rows if row[0] is not None]
