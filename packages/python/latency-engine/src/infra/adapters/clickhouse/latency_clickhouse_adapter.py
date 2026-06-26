from __future__ import annotations

import logging
from datetime import date

import clickhouse_connect

from shared.ports.latency_clickhouse_port import BaselineRow
from shared.tracing.tracer import api_span

logger = logging.getLogger(__name__)

_BASELINE_QUERY = """
SELECT
    checkpoint_date,
    p99_ttft_ms,
    p99_total_ms
FROM latency_checkpoints
WHERE model = %(model)s
  AND hour_of_day = %(hour_of_day)s
  AND checkpoint_date >= today() - %(days)s
ORDER BY checkpoint_date DESC
LIMIT %(days)s
"""


class LatencyClickHouseAdapter:
    """
    Read-only ClickHouse adapter for latency baseline queries.
    Implements LatencyClickHousePort structurally (Protocol).

    All IO is wrapped in child OTEL spans.
    No business logic — only query execution and row mapping.
    """

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
        """
        Queries latency_checkpoints for the given model and hour_of_day,
        returning up to `days` most-recent rows ordered by checkpoint_date DESC.
        Maps raw ClickHouse rows to BaselineRow dataclass instances.
        """
        with api_span(
            "clickhouse_adapter.get_baseline",
            {
                "db.system": "clickhouse",
                "db.operation": "SELECT",
                "db.name": "latency_checkpoints",
                "model": model,
                "hour_of_day": hour_of_day,
                "days": days,
            },
        ):
            try:
                result = self.client.query(
                    _BASELINE_QUERY,
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
                    # ClickHouse may return date as string or date object
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
