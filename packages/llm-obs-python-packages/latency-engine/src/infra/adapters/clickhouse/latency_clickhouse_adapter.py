"""
Algorithm Summary: Latency ClickHouse Analytics Read Adapter.
Provides read-only query access to ClickHouse latency checkpoints using clickhouse-connect driver.
Uses @traced_adapter decorator to capture trace_id context and record execution metrics without inline tracing boilerplate.
Transforms query result rows into BaselineRow value objects using functional map and filter pipelines.
"""
from __future__ import annotations
import logging
from datetime import date
import clickhouse_connect
from shared.ports.latency_clickhouse_port import BaselineRow
from shared.tracing.tracer import traced_adapter
from infra.adapters.clickhouse.models import LatencyCheckpointModel
from infra.adapters.clickhouse.queries import ClickHouseQueryRegistry

logger = logging.getLogger(__name__)

def _parse_baseline_row(raw_row: tuple) -> BaselineRow | None:
    try:
        chk_date, p99_ttft, p99_total = raw_row
        parsed_date = date.fromisoformat(chk_date) if isinstance(chk_date, str) else chk_date
        return BaselineRow(
            checkpoint_date=parsed_date,
            p99_ttft_ms=float(p99_ttft),
            p99_total_ms=float(p99_total),
        )
    except Exception as exc:
        logger.warning("Skipping malformed row %s: %s", raw_row, exc)
        return None

class LatencyClickHouseAdapter:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
    ) -> None:
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
    def get_baseline(
        self,
        model: str,
        hour_of_day: int,
        days: int,
    ) -> list[BaselineRow]:
        result = self.client.query(
            ClickHouseQueryRegistry.BASELINE_QUERY,
            {
                "model": model,
                "hour_of_day": hour_of_day,
                "days": days,
            },
        )
        parsed_rows = map(_parse_baseline_row, result.result_rows)
        return list(filter(lambda r: r is not None, parsed_rows))
