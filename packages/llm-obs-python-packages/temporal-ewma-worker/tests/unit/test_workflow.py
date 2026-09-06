import pytest
import sys
from temporalio import activity
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment
from worker.workflows import EwmaBaselineUpdate, EwmaWorkflowInput
from shared.types.ewma_types import EwmaRecord, ClusterCost, AnomalyPayload

active_pairs_mock = [("service-a", "model-b")]
get_baseline_mock_val: EwmaRecord | None = None
current_cost_mock_val: float = 10.0
global_avg_mock_val: float = 5.0
upsert_calls: list[EwmaRecord] = []
publish_calls: list[AnomalyPayload] = []
cluster_drilldown_calls: list[tuple[str, str]] = []


@activity.defn(name="fetch_active_pairs")
async def mock_fetch_active_pairs() -> list:
    print("mock_fetch_active_pairs called", file=sys.stderr)
    return active_pairs_mock


@activity.defn(name="fetch_cost_history")
async def mock_fetch_cost_history(service: str, model: str, hour_of_week: int) -> list:
    print("mock_fetch_cost_history called", file=sys.stderr)
    return []


@activity.defn(name="fetch_global_model_avg")
async def mock_fetch_global_model_avg(model: str, hour_of_week: int) -> float:
    print("mock_fetch_global_model_avg called", file=sys.stderr)
    return global_avg_mock_val


@activity.defn(name="fetch_current_cost_1h")
async def mock_fetch_current_cost_1h(service: str, model: str) -> float:
    print("mock_fetch_current_cost_1h called", file=sys.stderr)
    return current_cost_mock_val


@activity.defn(name="fetch_cost_by_cluster_1h")
async def mock_fetch_cost_by_cluster_1h(service: str, model: str) -> list:
    print("mock_fetch_cost_by_cluster_1h called", file=sys.stderr)
    cluster_drilldown_calls.append((service, model))
    return [ClusterCost(cluster_id="cluster-1", cost=current_cost_mock_val)]


@activity.defn(name="get_baseline")
async def mock_get_baseline(
    service: str, model: str, hour_of_week: int
) -> EwmaRecord | None:
    print(
        f"mock_get_baseline called, returning: {get_baseline_mock_val}", file=sys.stderr
    )
    return get_baseline_mock_val


@activity.defn(name="upsert_baseline")
async def mock_upsert_baseline(record: EwmaRecord) -> None:
    print("mock_upsert_baseline called", file=sys.stderr)
    upsert_calls.append(record)


@activity.defn(name="publish_anomaly_alert")
async def mock_publish_anomaly_alert(payload: AnomalyPayload) -> None:
    print("mock_publish_anomaly_alert called", file=sys.stderr)
    publish_calls.append(payload)


@pytest.mark.asyncio
async def test_workflow_cold_start() -> None:
    global get_baseline_mock_val, upsert_calls
    get_baseline_mock_val = None
    upsert_calls = []
    print("starting test_workflow_cold_start", file=sys.stderr)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-task-queue",
            workflows=[EwmaBaselineUpdate],
            activities=[
                mock_fetch_active_pairs,
                mock_fetch_cost_history,
                mock_fetch_global_model_avg,
                mock_fetch_current_cost_1h,
                mock_fetch_cost_by_cluster_1h,
                mock_get_baseline,
                mock_upsert_baseline,
                mock_publish_anomaly_alert,
            ],
        ):
            await env.client.execute_workflow(
                EwmaBaselineUpdate.run,
                EwmaWorkflowInput(force_hour=10),
                id="test-wf-cold",
                task_queue="test-task-queue",
            )

    assert len(upsert_calls) == 1
    assert upsert_calls[0].ewma_value == global_avg_mock_val
    assert upsert_calls[0].sample_count == 1
    assert upsert_calls[0].is_cold_start is True
    print("finished test_workflow_cold_start", file=sys.stderr)


@pytest.mark.asyncio
async def test_workflow_warm_no_anomaly() -> None:
    global get_baseline_mock_val, current_cost_mock_val, upsert_calls, publish_calls
    get_baseline_mock_val = EwmaRecord(
        service="service-a",
        model="model-b",
        hour_of_week=10,
        ewma_value=5.0,
        sample_count=8,
        is_cold_start=False,
    )
    current_cost_mock_val = 6.0
    upsert_calls = []
    publish_calls = []
    print("starting test_workflow_warm_no_anomaly", file=sys.stderr)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-task-queue",
            workflows=[EwmaBaselineUpdate],
            activities=[
                mock_fetch_active_pairs,
                mock_fetch_cost_history,
                mock_fetch_global_model_avg,
                mock_fetch_current_cost_1h,
                mock_fetch_cost_by_cluster_1h,
                mock_get_baseline,
                mock_upsert_baseline,
                mock_publish_anomaly_alert,
            ],
        ):
            await env.client.execute_workflow(
                EwmaBaselineUpdate.run,
                EwmaWorkflowInput(force_hour=10),
                id="test-wf-warm-ok",
                task_queue="test-task-queue",
            )

    assert len(upsert_calls) == 1
    assert upsert_calls[0].sample_count == 9
    assert len(publish_calls) == 0
    print("finished test_workflow_warm_no_anomaly", file=sys.stderr)


@pytest.mark.asyncio
async def test_workflow_warm_with_anomaly() -> None:
    global \
        get_baseline_mock_val, \
        current_cost_mock_val, \
        upsert_calls, \
        publish_calls, \
        cluster_drilldown_calls
    get_baseline_mock_val = EwmaRecord(
        service="service-a",
        model="model-b",
        hour_of_week=10,
        ewma_value=5.0,
        sample_count=8,
        is_cold_start=False,
    )
    current_cost_mock_val = 20.0
    upsert_calls = []
    publish_calls = []
    cluster_drilldown_calls = []
    print("starting test_workflow_warm_with_anomaly", file=sys.stderr)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-task-queue",
            workflows=[EwmaBaselineUpdate],
            activities=[
                mock_fetch_active_pairs,
                mock_fetch_cost_history,
                mock_fetch_global_model_avg,
                mock_fetch_current_cost_1h,
                mock_fetch_cost_by_cluster_1h,
                mock_get_baseline,
                mock_upsert_baseline,
                mock_publish_anomaly_alert,
            ],
        ):
            await env.client.execute_workflow(
                EwmaBaselineUpdate.run,
                EwmaWorkflowInput(force_hour=10),
                id="test-wf-warm-anomaly",
                task_queue="test-task-queue",
            )

    assert len(upsert_calls) == 1
    assert upsert_calls[0].sample_count == 9
    assert len(publish_calls) == 1
    assert publish_calls[0].current_cost == 20.0
    assert len(cluster_drilldown_calls) == 1
    print("finished test_workflow_warm_with_anomaly", file=sys.stderr)
