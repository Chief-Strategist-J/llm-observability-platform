import pytest
import sys
from datetime import timedelta
from temporalio import activity
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment
from worker.workflows import (
    WeeklyIntegrityCheck,
    IntegrityCheckInput,
    RetroactivePriceCorrection,
    RetroactiveCorrectionInput,
)

active_keys_mock = ["key1"]
verify_result_mock = {
    "dimension": "service",
    "key": "key1",
    "redis_sum": 100,
    "clickhouse_sum": 100,
    "is_mismatch": False,
}
spans_mock = [
    {
        "span_id": "span1",
        "model": "gpt-4",
        "provider": "openai",
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "cost_usd_micro": 50,
        "price_version": "v1.0",
    }
]
apply_corrections_mock_val = 1


@activity.defn(name="fetch_active_keys")
async def mock_fetch_active_keys(dimension: str) -> list:
    return active_keys_mock


@activity.defn(name="verify_key_integrity")
async def mock_verify_key_integrity(dimension: str, key: str) -> dict:
    return verify_result_mock


@activity.defn(name="fetch_spans_for_correction")
async def mock_fetch_spans_for_correction(hours: int) -> list:
    return spans_mock


@activity.defn(name="apply_price_corrections")
async def mock_apply_price_corrections(spans: list) -> int:
    return apply_corrections_mock_val


@pytest.mark.asyncio
async def test_weekly_integrity_check_workflow() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-task-queue-new",
            workflows=[WeeklyIntegrityCheck],
            activities=[
                mock_fetch_active_keys,
                mock_verify_key_integrity,
            ],
        ):
            res = await env.client.execute_workflow(
                WeeklyIntegrityCheck.run,
                IntegrityCheckInput(),
                id="test-wf-integrity",
                task_queue="test-task-queue-new",
            )
            assert "service" in res
            assert len(res["service"]) == 1
            assert res["service"][0]["key"] == "key1"


@pytest.mark.asyncio
async def test_retroactive_price_correction_workflow() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-task-queue-new",
            workflows=[RetroactivePriceCorrection],
            activities=[
                mock_fetch_spans_for_correction,
                mock_apply_price_corrections,
            ],
        ):
            res = await env.client.execute_workflow(
                RetroactivePriceCorrection.run,
                RetroactiveCorrectionInput(hours=24),
                id="test-wf-retroactive",
                task_queue="test-task-queue-new",
            )
            assert res == 1
