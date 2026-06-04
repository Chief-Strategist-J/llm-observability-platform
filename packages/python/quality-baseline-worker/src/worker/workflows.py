from datetime import timedelta
from temporalio import workflow
from features.quality_baseline.types import BaselineRecomputeResult

@workflow.defn(name="RecomputeQualityBaseline")
class RecomputeQualityBaseline:
    @workflow.run
    async def run(self) -> int:
        baselines = await workflow.execute_activity(
            "recompute_baseline_scores",
            start_to_close_timeout=timedelta(seconds=60),
        )
        count = await workflow.execute_activity(
            "write_redis_baselines",
            args=[baselines],
            start_to_close_timeout=timedelta(seconds=30),
        )
        return count

@workflow.defn(name="RollupQualityTrend")
class RollupQualityTrend:
    @workflow.run
    async def run(self) -> int:
        count = await workflow.execute_activity(
            "rollup_quality_trend",
            start_to_close_timeout=timedelta(seconds=120),
        )
        return count
