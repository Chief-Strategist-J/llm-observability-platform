import pytest
from datetime import timedelta
from temporalio import activity
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment
from worker.workflows import RecomputeQualityBaseline, RollupQualityTrend
from features.quality_baseline.types import BaselineRecomputeResult

baselines_mock_val = [
    BaselineRecomputeResult(model="m1", endpoint="e1", prompt_type="p1", avg_score=0.8, sample_count=5)
]

@activity.defn(name="recompute_baseline_scores")
async def mock_recompute_baseline_scores() -> list:
    return baselines_mock_val

@activity.defn(name="write_redis_baselines")
async def mock_write_redis_baselines(baselines: list) -> int:
    return len(baselines)

@activity.defn(name="rollup_quality_trend")
async def mock_rollup_quality_trend() -> int:
    return 10

@pytest.mark.asyncio
async def test_recompute_workflow() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-quality-queue",
            workflows=[RecomputeQualityBaseline],
            activities=[
                mock_recompute_baseline_scores,
                mock_write_redis_baselines,
            ],
        ):
            count = await env.client.execute_workflow(
                RecomputeQualityBaseline.run,
                id="test-recompute-wf",
                task_queue="test-quality-queue",
            )
            assert count == 1

@pytest.mark.asyncio
async def test_rollup_workflow() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-quality-queue",
            workflows=[RollupQualityTrend],
            activities=[
                mock_rollup_quality_trend,
            ],
        ):
            count = await env.client.execute_workflow(
                RollupQualityTrend.run,
                id="test-rollup-wf",
                task_queue="test-quality-queue",
            )
            assert count == 10
