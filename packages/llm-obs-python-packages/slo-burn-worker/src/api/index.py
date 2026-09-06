import time
from typing import Any
from temporalio.client import Client
from worker.config import load_config


async def health(env: dict[str, str] | None = None) -> dict[str, Any]:
    cfg = load_config(env)
    return {
        "status": "ok",
        "temporal_host": cfg.temporal_host,
        "temporal_namespace": cfg.temporal_namespace,
        "temporal_task_queue": cfg.temporal_task_queue,
        "redis_url": cfg.redis_url,
        "kafka_bootstrap_servers": cfg.kafka_bootstrap_servers,
    }


async def trigger_workflow(env: dict[str, str] | None = None) -> dict[str, Any]:
    cfg = load_config(env)
    client = await Client.connect(cfg.temporal_host, namespace=cfg.temporal_namespace)
    workflow_id = f"slo-burn-manual-{int(time.time())}"

    handle = await client.start_workflow(
        "SloBurnWorkflow",
        id=workflow_id,
        task_queue=cfg.temporal_task_queue,
    )

    return {
        "status": "triggered",
        "workflow_id": workflow_id,
        "run_id": handle.first_execution_run_id,
    }
