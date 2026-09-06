from typing import List, Tuple
from datetime import datetime
import clickhouse_connect
from shared.ports.clickhouse_port import ClickHousePort


class ClickHouseAdapter(ClickHousePort):
    def __init__(
        self, host: str, port: int, username: str, password: str, database: str
    ):
        self.client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
        )

    def fetch_cost_series_raw(
        self, lookback_hours: int
    ) -> List[Tuple[str, str, datetime, float]]:
        # Using string formatting for lookback_hours interval safely as it is a validated int
        query = f"""
        SELECT
          service_name,
          model,
          toStartOfHour(ts) AS hour_bucket,
          sum(cost_usd_micro) AS total_cost_micro
        FROM cost_by_dimension
        WHERE dimension = 'model'
          AND ts > now() - INTERVAL {int(lookback_hours)} HOUR
        GROUP BY service_name, model, hour_bucket
        ORDER BY service_name, model, hour_bucket
        """
        result = self.client.query(query)
        rows: List[Tuple[str, str, datetime, float]] = []
        for row in result.result_rows:
            service_name = str(row[0])
            model = str(row[1])
            hour_bucket = row[2]  # typically datetime object returned by clickhouse-connect
            total_cost = float(row[3])
            rows.append((service_name, model, hour_bucket, total_cost))
        return rows

    def fetch_latency_series_raw(
        self, lookback_hours: int
    ) -> List[Tuple[str, str, datetime, float]]:
        query = f"""
        SELECT
          service_name,
          model,
          toStartOfHour(timestamp_utc) AS hour_bucket,
          avg(latency_ms_total) AS avg_latency
        FROM llm_spans
        WHERE timestamp_utc > now() - INTERVAL {int(lookback_hours)} HOUR
        GROUP BY service_name, model, hour_bucket
        ORDER BY service_name, model, hour_bucket
        """
        result = self.client.query(query)
        rows: List[Tuple[str, str, datetime, float]] = []
        for row in result.result_rows:
            service_name = str(row[0])
            model = str(row[1])
            hour_bucket = row[2]
            avg_latency = float(row[3])
            rows.append((service_name, model, hour_bucket, avg_latency))
        return rows

