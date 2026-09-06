import time
from temporalio.client import Client
from worker.config import load_config
from worker.workflows import EwmaWorkflowInput


async def health(env: dict[str, str] | None = None) -> dict:
    cfg = load_config(env)
    return {
        "status": "ok",
        "temporal_host": cfg.temporal_host,
        "temporal_namespace": cfg.temporal_namespace,
        "temporal_task_queue": cfg.temporal_task_queue,
        "redis_url": cfg.redis_url,
        "kafka_bootstrap_servers": cfg.kafka_bootstrap_servers,
    }


async def trigger_workflow(
    force_hour: int | None = None, env: dict[str, str] | None = None
) -> dict:
    cfg = load_config(env)
    client = await Client.connect(cfg.temporal_host, namespace=cfg.temporal_namespace)
    workflow_id = f"ewma-update-manual-{int(time.time())}"

    workflow_input = (
        EwmaWorkflowInput(force_hour=force_hour) if force_hour is not None else None
    )

    handle = await client.start_workflow(
        "EwmaBaselineUpdate",
        id=workflow_id,
        task_queue=cfg.temporal_task_queue,
        args=[workflow_input] if workflow_input else [],
    )

    return {
        "status": "triggered",
        "workflow_id": workflow_id,
        "run_id": handle.first_execution_run_id,
    }
