from __future__ import annotations
import logging
from datetime import date
import clickhouse_connect
from shared.ports.latency_clickhouse_port import BaselineRow
from shared.tracing.tracer import api_span
from infra.adapters.clickhouse.queries import LatencyCheckpointModel, ClickHouseQueryRegistry

logger = logging.getLogger(__name__)

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
        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                database=self._database,
            )
        return self._client

    def get_baseline(
        self,
        model: str,
        hour_of_day: int,
        days: int,
    ) -> list[BaselineRow]:
        table_name = LatencyCheckpointModel.table_name()
        with api_span(
            "clickhouse_adapter.get_baseline",
            {
                "db.system": "clickhouse",
                "db.operation": "SELECT",
                "db.name": table_name,
                "model": model,
                "hour_of_day": hour_of_day,
                "days": days,
            },
        ):
            try:
                result = self.client.query(
                    ClickHouseQueryRegistry.BASELINE_QUERY,
                    {
                        "model": model,
                        "hour_of_day": hour_of_day,
                        "days": days,
                    },
                )
            except Exception as exc:
                logger.error(
                    "ClickHouse query failed for model=%s hour=%s: %s",
                    model,
                    hour_of_day,
                    exc,
                )
                raise

            rows: list[BaselineRow] = []
            for raw_row in result.result_rows:
                try:
                    checkpoint_date, p99_ttft, p99_total = raw_row
                    if isinstance(checkpoint_date, str):
                        checkpoint_date = date.fromisoformat(checkpoint_date)
                    rows.append(
                        BaselineRow(
                            checkpoint_date=checkpoint_date,
                            p99_ttft_ms=float(p99_ttft),
                            p99_total_ms=float(p99_total),
                        )
                    )
                except Exception as exc:
                    logger.warning("Skipping malformed row %s: %s", raw_row, exc)

            return rows
