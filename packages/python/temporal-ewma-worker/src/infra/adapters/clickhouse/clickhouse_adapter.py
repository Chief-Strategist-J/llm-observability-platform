from typing import List, Tuple
import clickhouse_connect
from shared.ports.clickhouse_port import ClickHousePort
from shared.types.ewma_types import ClusterCost


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

    def get_active_pairs(self) -> List[Tuple[str, str]]:
        query = """
        SELECT DISTINCT service, model
        FROM cost_by_dimension
        WHERE timestamp >= now() - INTERVAL 7 DAY
        """
        result = self.client.query(query)
        return [(str(row[0]), str(row[1])) for row in result.result_rows]

    def get_cost_history(
        self, service: str, model: str, hour_of_week: int
    ) -> List[float]:
        query = """
        SELECT sum(cost) as hourly_cost
        FROM cost_by_dimension
        WHERE service = %(service)s
          AND model = %(model)s
          AND ((toDayOfWeek(timestamp) - 1) * 24 + toHour(timestamp)) = %(hour_of_week)s
          AND timestamp >= now() - INTERVAL 28 DAY
        GROUP BY toStartOfHour(timestamp)
        ORDER BY toStartOfHour(timestamp) DESC
        LIMIT 4
        """
        result = self.client.query(
            query, {"service": service, "model": model, "hour_of_week": hour_of_week}
        )
        return [float(row[0]) for row in result.result_rows if row[0] is not None]

    def get_global_model_avg(self, model: str, hour_of_week: int) -> float:
        query = """
        SELECT avg(hourly_cost)
        FROM (
            SELECT sum(cost) as hourly_cost
            FROM cost_by_dimension
            WHERE model = %(model)s
              AND ((toDayOfWeek(timestamp) - 1) * 24 + toHour(timestamp)) = %(hour_of_week)s
              AND timestamp >= now() - INTERVAL 28 DAY
            GROUP BY toStartOfHour(timestamp)
        )
        """
        result = self.client.query(
            query, {"model": model, "hour_of_week": hour_of_week}
        )
        rows = result.result_rows
        if rows and rows[0][0] is not None:
            return float(rows[0][0])
        return 0.0

    def get_current_cost_1h(self, service: str, model: str) -> float:
        query = """
        SELECT sum(cost)
        FROM cost_by_dimension
        WHERE service = %(service)s
          AND model = %(model)s
          AND timestamp >= now() - INTERVAL 1 HOUR
        """
        result = self.client.query(query, {"service": service, "model": model})
        rows = result.result_rows
        if rows and rows[0][0] is not None:
            return float(rows[0][0])
        return 0.0

    def get_cost_by_cluster_1h(self, service: str, model: str) -> List[ClusterCost]:
        query = """
        SELECT cluster_id, sum(cost) as cost
        FROM cost_by_dimension
        WHERE service = %(service)s
          AND model = %(model)s
          AND timestamp >= now() - INTERVAL 1 HOUR
        GROUP BY cluster_id
        """
        result = self.client.query(query, {"service": service, "model": model})
        return [
            ClusterCost(cluster_id=str(row[0]), cost=float(row[1]))
            for row in result.result_rows
            if row[0] is not None and row[1] is not None
        ]

    def get_active_keys(self, dimension: str) -> List[str]:
        if dimension == "service":
            query = "SELECT DISTINCT service_name FROM llm_spans WHERE timestamp_utc >= now() - INTERVAL 1 HOUR"
        elif dimension == "model":
            query = "SELECT DISTINCT model FROM llm_spans WHERE timestamp_utc >= now() - INTERVAL 1 HOUR"
        elif dimension == "user":
            query = "SELECT DISTINCT user_id FROM llm_spans WHERE user_id IS NOT NULL AND user_id != '' AND timestamp_utc >= now() - INTERVAL 1 HOUR"
        else:
            return []
        result = self.client.query(query)
        return [str(row[0]) for row in result.result_rows if row[0] is not None]

    def get_clickhouse_sum_1h(self, dimension: str, key: str) -> int:
        if dimension == "service":
            query = "SELECT sum(cost_usd_micro) FROM llm_spans WHERE service_name = %(key)s AND timestamp_utc >= now() - INTERVAL 1 HOUR"
        elif dimension == "model":
            query = "SELECT sum(cost_usd_micro) FROM llm_spans WHERE model = %(key)s AND timestamp_utc >= now() - INTERVAL 1 HOUR"
        elif dimension == "user":
            query = "SELECT sum(cost_usd_micro) FROM llm_spans WHERE user_id = %(key)s AND timestamp_utc >= now() - INTERVAL 1 HOUR"
        else:
            return 0
        result = self.client.query(query, {"key": key})
        rows = result.result_rows
        if rows and rows[0][0] is not None:
            return int(rows[0][0])
        return 0

    def get_spans_for_correction(self, hours: int) -> List[dict]:
        query = """
        SELECT span_id, model, provider, prompt_tokens, completion_tokens, cost_usd_micro, price_version
        FROM llm_spans
        WHERE timestamp_utc >= now() - INTERVAL %(hours)s HOUR
        """
        result = self.client.query(query, {"hours": hours})
        spans = []
        for row in result.result_rows:
            spans.append({
                "span_id": str(row[0]),
                "model": str(row[1]),
                "provider": str(row[2]),
                "prompt_tokens": int(row[3]),
                "completion_tokens": int(row[4]),
                "cost_usd_micro": int(row[5]),
                "price_version": str(row[6])
            })
        return spans

    def insert_correction_rows(self, rows: List[dict]) -> None:
        if not rows:
            return
        data = []
        column_names = [
            "span_id", "trace_id", "parent_span_id", "schema_version",
            "model", "provider", "service_name", "endpoint", "environment",
            "user_id", "session_id", "prompt_tokens", "completion_tokens",
            "latency_ms_ttft", "latency_ms_total", "finish_reason",
            "cost_usd_micro", "price_version", "token_count_method",
            "is_sampled", "retry_count", "attempted_models", "pii_detected",
            "injection_attempt", "timestamp_utc"
        ]
        for r in rows:
            data.append([
                r.get("span_id"),
                r.get("trace_id"),
                r.get("parent_span_id"),
                r.get("schema_version", 1),
                r.get("model", ""),
                r.get("provider", ""),
                r.get("service_name", ""),
                r.get("endpoint", ""),
                r.get("environment", "production"),
                r.get("user_id"),
                r.get("session_id"),
                r.get("prompt_tokens", 0),
                r.get("completion_tokens", 0),
                r.get("latency_ms_ttft"),
                r.get("latency_ms_total", 0),
                r.get("finish_reason", "stop"),
                r.get("cost_usd_micro", 0),
                r.get("price_version", ""),
                r.get("token_count_method", "estimated"),
                r.get("is_sampled", 0),
                r.get("retry_count", 0),
                r.get("attempted_models", []),
                r.get("pii_detected", 0),
                r.get("injection_attempt", 0),
                r.get("timestamp_utc")
            ])
        self.client.insert("llm_spans", data, column_names=column_names)

