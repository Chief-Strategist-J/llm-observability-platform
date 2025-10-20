"""Logs Pipeline Worker Module.

This module provides a Temporal worker for the logs pipeline system. It connects to a
Temporal server and runs workflows and activities related to logs pipeline operations,
specifically handling Loki, Promtail, and Grafana container startup tasks.

"""

import asyncio
from pathlib import Path
import sys

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from temporalio.client import Client
from temporalio.worker import Worker

from infrastructure.orchestrator.activities.common_activity.grafana_activity import (
    configure_grafana,
    start_grafana_container,
)
from infrastructure.orchestrator.activities.common_activity.loki_activity import (
    start_loki_container,
)
from infrastructure.orchestrator.activities.common_activity.promtail_activity import (
    start_promtail_container,
)
from infrastructure.orchestrator.workflows.logs_pipeline_workflow import (
    LogsPipelineWorkflow,
)


async def main() -> None:
    """Main entry point for the logs pipeline worker.

    Connects to the Temporal server at localhost:7233 and starts a worker that processes
    logs pipeline tasks. The worker handles the LogsPipelineWorkflow and all logs-
    related activities (Loki, Promtail, Grafana).

    The worker runs indefinitely until manually stopped, processing tasks from the
    'logs-pipeline-queue' task queue.

    """
    client = await Client.connect("localhost:7233")

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

    print("Logs Pipeline Worker started. Task Queue: logs-pipeline-queue")
    print("Listening for workflows: LogsPipelineWorkflow")
    print("Press Ctrl+C to stop the worker")

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
