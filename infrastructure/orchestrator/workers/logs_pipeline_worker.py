# file: infrastructure/orchestrator/workers/logs_pipeline_worker.py
from __future__ import annotations

"""
Worker entrypoint for Logs Pipeline.
- awaits Client.connect(...)
- constructs Worker and runs it
- safely closes Temporal client on exit
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Ensure project root on sys.path for local imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio.client import Client
from temporalio.worker import Worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _maybe_close_client(client: object) -> None:
    if client is None:
        return
    close_attr = getattr(client, "close", None)
    if close_attr is None or not callable(close_attr):
        return
    try:
        result = close_attr()
    except TypeError:
        try:
            result = await close_attr
        except Exception:
            return
    if asyncio.iscoroutine(result):
        try:
            await result
        except Exception:
            logger.exception("Error while awaiting client.close()")


async def main() -> None:
    temporal_host = "localhost:7233"
    task_queue = "logs-pipeline-queue"
    client: Optional[Client] = None
    worker: Optional[Worker] = None

    try:
        logger.info("Connecting to Temporal server at %s", temporal_host)
        client = await Client.connect(temporal_host)
        logger.info("Connected to Temporal server")
        logger.info("Starting Logs Pipeline Worker...")

        # delayed imports (sys.path already set)
        from infrastructure.orchestrator.workflows.logs_pipeline_workflow import LogsPipelineWorkflow
        from infrastructure.orchestrator.activities.configurations_activity.loki_activity import (
            start_loki_activity,
            stop_loki_activity,
            restart_loki_activity,
            delete_loki_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.promtail_activity import (
            start_promtail_activity,
            stop_promtail_activity,
            restart_promtail_activity,
            delete_promtail_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.prometheus_activity import (
            start_prometheus_activity,
            stop_prometheus_activity,
            restart_prometheus_activity,
            delete_prometheus_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.grafana_activity import (
            start_grafana_activity,
            stop_grafana_activity,
            restart_grafana_activity,
            delete_grafana_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.jaeger_activity import (
            start_jaeger_activity,
            stop_jaeger_activity,
            restart_jaeger_activity,
            delete_jaeger_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.opentelemetry_collector import (
            start_opentelemetry_collector,
            stop_opentelemetry_collector,
            restart_opentelemetry_collector,
            delete_opentelemetry_collector,
        )
        from infrastructure.orchestrator.activities.configurations_activity.neo4j_activity import (
            start_neo4j_activity,
            stop_neo4j_activity,
            restart_neo4j_activity,
            delete_neo4j_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.qdrant_activity import (
            start_qdrant_activity,
            stop_qdrant_activity,
            restart_qdrant_activity,
            delete_qdrant_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.redis_activity import (
            start_redis_activity,
            stop_redis_activity,
            restart_redis_activity,
            delete_redis_activity,
        )
        

        worker = Worker(
            client,
            task_queue=task_queue,
            workflows=[LogsPipelineWorkflow],
            activities=[
                start_loki_activity, 
                stop_loki_activity, 
                restart_loki_activity, 
                delete_loki_activity,
                start_promtail_activity,
                stop_promtail_activity,
                restart_promtail_activity,
                delete_promtail_activity,
                start_prometheus_activity,
                stop_prometheus_activity,
                restart_prometheus_activity,
                delete_prometheus_activity,
                start_grafana_activity,
                stop_grafana_activity,
                restart_grafana_activity,
                delete_grafana_activity,
                start_jaeger_activity,
                stop_jaeger_activity,
                restart_jaeger_activity,
                delete_jaeger_activity,
                start_opentelemetry_collector,
                stop_opentelemetry_collector,
                restart_opentelemetry_collector,
                delete_opentelemetry_collector,
                start_neo4j_activity,
                stop_neo4j_activity,
                restart_neo4j_activity,
                delete_neo4j_activity,
                start_qdrant_activity,
                stop_qdrant_activity,
                restart_qdrant_activity,
                delete_qdrant_activity,
                start_redis_activity,
                stop_redis_activity,
                restart_redis_activity,
                delete_redis_activity,
            ],
        )

        logger.info("Worker ready. Queue: %s", task_queue)
        await worker.run()

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Worker received shutdown signal")
    except Exception:
        logger.exception("Worker encountered error")
        raise
    finally:
        if worker is not None:
            logger.info("Worker shutdown requested")
        if client is not None:
            logger.info("Closing Temporal client connection")
            try:
                await _maybe_close_client(client)
                logger.info("Temporal client connection closed")
            except Exception:
                logger.exception("Error while closing Temporal client")


if __name__ == "__main__":
    asyncio.run(main())
