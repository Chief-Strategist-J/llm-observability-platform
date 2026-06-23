import pytest
from temporalio import activity
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment
from worker.workflows import LatencyBaselineWorkflow

@activity.defn(name="hourly_checkpoint")
async def mock_hourly_checkpoint(target_date_str: str | None = None, target_hour: int | None = None) -> int:
    return 5

@pytest.mark.asyncio
async def test_latency_baseline_workflow() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-latency-queue",
            workflows=[LatencyBaselineWorkflow],
            activities=[mock_hourly_checkpoint],
        ):
            count = await env.client.execute_workflow(
                LatencyBaselineWorkflow.run,
                id="test-latency-wf",
                task_queue="test-latency-queue",
            )
            assert count == 5
