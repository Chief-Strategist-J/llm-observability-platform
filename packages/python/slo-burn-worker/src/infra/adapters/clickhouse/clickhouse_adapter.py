import logging
import clickhouse_connect
from shared.ports.clickhouse_port import ClickHousePort
from shared.tracing.tracer import trace_span

logger = logging.getLogger(__name__)

class ClickHouseAdapter(ClickHousePort):
    def __init__(self, host: str, port: int, username: str, password: str, database: str):
        self.client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
        )

    def get_baseline_p95_7d(self, model: str, endpoint: str) -> float:
        # Try query latency_checkpoints first
        try:
            with trace_span(
                "clickhouse:get_baseline_p95_7d",
                attributes={
                    "db.system": "clickhouse",
                    "model": model,
                    "endpoint": endpoint,
                },
            ):
                query = """
                SELECT p95
                FROM latency_checkpoints
                WHERE model = %(model)s
                  AND endpoint = %(endpoint)s
                  AND timestamp >= now() - INTERVAL 7 DAY
                ORDER BY timestamp DESC
                LIMIT 1
                """
                result = self.client.query(query, {"model": model, "endpoint": endpoint})
                rows = result.result_rows
                if rows and rows[0][0] is not None:
                    return float(rows[0][0])
        except Exception as e:
            logger.info(
                "Failed to fetch baseline P95 from latency_checkpoints table, falling back to raw spans: %s",
                e,
            )

        # Fallback to computing from raw llm_spans
        try:
            with trace_span(
                "clickhouse:get_baseline_p95_7d_fallback",
                attributes={
                    "db.system": "clickhouse",
                    "model": model,
                    "endpoint": endpoint,
                },
            ):
                fallback_query = """
                SELECT quantile(0.95)(latency_ms_total)
                FROM llm_spans
                WHERE model = %(model)s
                  AND endpoint = %(endpoint)s
                  AND timestamp_utc >= now() - INTERVAL 7 DAY
                """
                result = self.client.query(fallback_query, {"model": model, "endpoint": endpoint})
                rows = result.result_rows
                if rows and rows[0][0] is not None:
                    return float(rows[0][0])
        except Exception as e:
            logger.error("Failed to compute fallback baseline P95 from llm_spans: %s", e)

        return 0.0
