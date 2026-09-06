import pytest
from temporalio import activity
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment
from worker.workflows import SloBurnWorkflow

active_pairs_mock = [("gpt-4o", "/v1/chat/completions")]
compute_burn_rates_calls = []
write_burn_rates_calls = []
handle_alerts_calls = []

@activity.defn(name="fetch_active_pairs")
async def mock_fetch_active_pairs() -> list:
    return active_pairs_mock

@activity.defn(name="compute_burn_rates")
async def mock_compute_burn_rates(model: str, endpoint: str, unix_ts: int) -> dict:
    compute_burn_rates_calls.append((model, endpoint, unix_ts))
    return {"fast": 15.0, "medium": 8.0, "slow": 4.0}

@activity.defn(name="write_burn_rates")
async def mock_write_burn_rates(model: str, endpoint: str, burn_rates_dict: dict) -> None:
    write_burn_rates_calls.append((model, endpoint, burn_rates_dict))

@activity.defn(name="handle_alerts")
async def mock_handle_alerts(model: str, endpoint: str, burn_rates_dict: dict, unix_ts: int) -> None:
    handle_alerts_calls.append((model, endpoint, burn_rates_dict, unix_ts))

@pytest.mark.asyncio
async def test_workflow_runs_activities() -> None:
    global compute_burn_rates_calls, write_burn_rates_calls, handle_alerts_calls
    compute_burn_rates_calls = []
    write_burn_rates_calls = []
    handle_alerts_calls = []

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-slo-task-queue",
            workflows=[SloBurnWorkflow],
            activities=[
                mock_fetch_active_pairs,
                mock_compute_burn_rates,
                mock_write_burn_rates,
                mock_handle_alerts,
            ],
        ):
            await env.client.execute_workflow(
                SloBurnWorkflow.run,
                id="test-slo-wf",
                task_queue="test-slo-task-queue",
            )

    assert len(compute_burn_rates_calls) == 1
    assert compute_burn_rates_calls[0][0] == "gpt-4o"
    assert compute_burn_rates_calls[0][1] == "/v1/chat/completions"

    assert len(write_burn_rates_calls) == 1
    assert write_burn_rates_calls[0][2]["fast"] == 15.0

    assert len(handle_alerts_calls) == 1
    assert handle_alerts_calls[0][0] == "gpt-4o"
