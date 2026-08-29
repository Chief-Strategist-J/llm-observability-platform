"""
Algorithm Summary: Infrastructure ClickHouse Adapter.
Provides direct ClickHouse database access using clickhouse-connect driver. Uses @traced_adapter
to automatically attach trace_id and span context without repetitive inline tracing code blocks.
Executes batch insertions of latency checkpoints and historical percentile queries using functional mapping pipelines.
"""
from __future__ import annotations
import clickhouse_connect
from shared.ports.clickhouse_port import ClickHousePort
from shared.tracing.tracer import traced_adapter
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
        self._client = self._client or clickhouse_connect.get_client(
            host=self._host,
            port=self._port,
            username=self._username,
            password=self._password,
            database=self._database,
        )
        return self._client

    @traced_adapter("clickhouse")
    def insert_latency_checkpoints(self, rows: list[tuple]) -> None:
        rows and self.client.insert(
            LatencyCheckpointModel.table_name(),
            list(map(list, rows)),
            column_names=LatencyCheckpointModel.column_names(),
        )

    @traced_adapter("clickhouse")
    def get_p99_ttft_history_7d(self, model: str, endpoint: str, hour_of_day: int) -> list[float]:
        result = self.client.query(
            ClickHouseQueryRegistry.P99_TTFT_HISTORY_QUERY,
            {"model": model, "endpoint": endpoint, "hour_of_day": hour_of_day},
        )
        return list(map(float, filter(lambda val: val is not None, map(lambda r: r[0], result.result_rows))))
