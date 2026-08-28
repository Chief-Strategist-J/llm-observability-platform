from datetime import date
from temporalio import activity
from shared.ports.clickhouse_port import ClickHousePort
from shared.ports.redis_port import RedisPort
from shared.ports.kafka_producer_port import KafkaProducerPort
from features.latency_baseline.service import LatencyBaselineService

class LatencyBaselineActivities:
    def __init__(
        self,
        clickhouse: ClickHousePort,
        redis: RedisPort,
        kafka: KafkaProducerPort
    ) -> None:
        self.clickhouse = clickhouse
        self.redis = redis
        self.kafka = kafka

    @activity.defn(name="hourly_checkpoint")
    async def hourly_checkpoint(
        self,
        target_date_str: str | None = None,
        target_hour: int | None = None
    ) -> int:
        target_date = None
        if target_date_str:
            try:
                target_date = date.fromisoformat(target_date_str)
            except ValueError:
                pass
        
        # Run service logic
        return LatencyBaselineService.run_hourly_checkpoint(
            redis=self.redis,
            clickhouse=self.clickhouse,
            kafka=self.kafka,
            target_date=target_date,
            target_hour=target_hour
        )
