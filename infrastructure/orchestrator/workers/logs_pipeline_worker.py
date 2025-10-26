"""Logs Pipeline Worker Module.

This module provides a Temporal worker for the logs pipeline system. It connects to a
Temporal server and runs workflows and activities related to logs pipeline operations,
specifically handling Loki, Promtail, and Grafana container startup tasks.

"""

import asyncio
import logging
from pathlib import Path
import sys

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from temporalio.client import Client
from temporalio.worker import Worker

from infrastructure.orchestrator.activities.common_activity.configure_grafana_activity import (
    configure_grafana,
)
from infrastructure.orchestrator.activities.common_activity.loki_activity import (
    start_loki_container,
)
from infrastructure.orchestrator.activities.common_activity.promtail_activity import (
    start_promtail_container,
)
from infrastructure.orchestrator.activities.common_activity.start_grafana_activity import (
    start_grafana_container,
)
from infrastructure.orchestrator.workflows.logs_pipeline_workflow import (
    LogsPipelineWorkflow,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point for the logs pipeline worker.

    Connects to the Temporal server at localhost:7233 and starts a worker that processes
    logs pipeline tasks. The worker handles the LogsPipelineWorkflow and all logs-
    related activities (Loki, Promtail, Grafana).

    The worker runs indefinitely until manually stopped, processing tasks from the
    'logs-pipeline-queue' task queue.

    """
    client = None
    worker = None

    try:
        logger.info("Attempting to connect to Temporal server at localhost:7233")
        client = await Client.connect("localhost:7233")
        logger.info("Successfully connected to Temporal server")

        logger.info("Initializing Logs Pipeline Worker")
        worker = Worker(
            client,
            task_queue="logs-pipeline-queue",
            workflows=[LogsPipelineWorkflow],
            activities=[
                start_loki_container,
                start_promtail_container,
                start_grafana_container,
                configure_grafana,
            ],
        )

        logger.info("Logs Pipeline Worker started. Task Queue: logs-pipeline-queue")
        logger.info("Listening for workflows: LogsPipelineWorkflow")
        logger.info(
            "Available activities: start_loki_container, start_promtail_container, start_grafana_container, configure_grafana"
        )
        logger.info("Press Ctrl+C to stop the worker")

        await worker.run()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down gracefully...")
    except Exception as e:
        logger.error(f"Worker encountered an error: {e}", exc_info=True)
        raise
    finally:
        if worker:
            logger.info("Stopping Logs Pipeline Worker")
        if client:
            logger.info("Closing Temporal client connection")
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
