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
