from typing import List, Tuple
from temporalio import activity
from shared.ports.clickhouse_port import ClickHousePort
from shared.ports.redis_port import RedisPort
from shared.ports.postgres_port import PostgresPort
from shared.ports.alert_publisher_port import AlertPublisherPort
from shared.types.ewma_types import EwmaRecord, ClusterCost, AnomalyPayload


class EwmaActivities:
    def __init__(
        self,
        clickhouse: ClickHousePort,
        redis: RedisPort,
        postgres: PostgresPort,
        alert_publisher: AlertPublisherPort,
    ):
        self.clickhouse = clickhouse
        self.redis = redis
        self.postgres = postgres
        self.alert_publisher = alert_publisher

    @activity.defn(name="fetch_active_pairs")
    async def fetch_active_pairs(self) -> List[Tuple[str, str]]:
        return self.clickhouse.get_active_pairs()

    @activity.defn(name="fetch_cost_history")
    async def fetch_cost_history(
        self, service: str, model: str, hour_of_week: int
    ) -> List[float]:
        return self.clickhouse.get_cost_history(service, model, hour_of_week)

    @activity.defn(name="fetch_global_model_avg")
    async def fetch_global_model_avg(self, model: str, hour_of_week: int) -> float:
        return self.clickhouse.get_global_model_avg(model, hour_of_week)

    @activity.defn(name="fetch_current_cost_1h")
    async def fetch_current_cost_1h(self, service: str, model: str) -> float:
        return self.clickhouse.get_current_cost_1h(service, model)

    @activity.defn(name="fetch_cost_by_cluster_1h")
    async def fetch_cost_by_cluster_1h(
        self, service: str, model: str
    ) -> List[ClusterCost]:
        return self.clickhouse.get_cost_by_cluster_1h(service, model)

    @activity.defn(name="get_baseline")
    async def get_baseline(
        self, service: str, model: str, hour_of_week: int
    ) -> EwmaRecord | None:
        return self.postgres.get_baseline(service, model, hour_of_week)

    @activity.defn(name="upsert_baseline")
    async def upsert_baseline(self, record: EwmaRecord) -> None:
        self.postgres.upsert_baseline(record)
        self.redis.set_ewma(
            record.service, record.model, record.hour_of_week, record.ewma_value
        )

    @activity.defn(name="publish_anomaly_alert")
    async def publish_anomaly_alert(self, payload: AnomalyPayload) -> None:
        self.alert_publisher.publish_anomaly(payload)
