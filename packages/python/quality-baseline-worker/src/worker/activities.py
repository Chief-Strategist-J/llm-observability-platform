from typing import List
from temporalio import activity
from shared.ports.clickhouse_port import ClickHousePort
from shared.ports.redis_port import RedisPort
from shared.ports.postgres_port import PostgresPort
from shared.ports.metrics_port import MetricsPort
from features.quality_baseline.types import BaselineRecomputeResult
from features.quality_baseline.service import QualityBaselineService

class QualityBaselineActivities:
    def __init__(
        self,
        clickhouse: ClickHousePort,
        redis: RedisPort,
        postgres: PostgresPort,
        metrics: MetricsPort,
    ):
        self.clickhouse = clickhouse
        self.redis = redis
        self.postgres = postgres
        self.metrics = metrics

    @activity.defn(name="recompute_baseline_scores")
    async def recompute_baseline_scores(self) -> List[BaselineRecomputeResult]:
        return self.postgres.get_rolling_baselines()

    @activity.defn(name="write_redis_baselines")
    async def write_redis_baselines(self, baselines: List[BaselineRecomputeResult]) -> int:
        for b in baselines:
            self.redis.set_baseline_quality(
                model=b.model,
                endpoint=b.endpoint,
                prompt_type=b.prompt_type,
                score=b.avg_score
            )
        self.metrics.record_baseline_updates(len(baselines))
        return len(baselines)

    @activity.defn(name="rollup_quality_trend")
    async def rollup_quality_trend(self) -> int:
        return QualityBaselineService.rollup_yesterday_scores(
            postgres=self.postgres,
            clickhouse=self.clickhouse,
            metrics=self.metrics
        )
