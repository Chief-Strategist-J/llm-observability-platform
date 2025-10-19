"""Metrics Pipeline Worker Module.

This module provides a Temporal worker for the metrics pipeline system. It connects to a
Temporal server and runs workflows and activities related to metrics pipeline
operations, specifically handling Prometheus and Grafana container startup tasks.

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
    start_grafana_container,
)
from infrastructure.orchestrator.activities.common_activity.prometheus_activity import (
    start_prometheus_container,
)
from infrastructure.orchestrator.workflows.metrics_pipeline_workflow import (
    MetricsPipelineWorkflow,
)


async def main() -> None:
    """Main entry point for the metrics pipeline worker.

    Connects to the Temporal server at localhost:7233 and starts a worker that processes
    metrics pipeline tasks. The worker handles the MetricsPipelineWorkflow and all
    metrics-related activities (Prometheus, Grafana).

    The worker runs indefinitely until manually stopped, processing tasks from the
    'metrics-pipeline-queue' task queue.

    """
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="metrics-pipeline-queue",
        workflows=[MetricsPipelineWorkflow],
        activities=[
            start_prometheus_container,
            start_grafana_container,
        ],
    )

    print("Metrics Pipeline Worker started. Task Queue: metrics-pipeline-queue")
    print("Listening for workflows: MetricsPipelineWorkflow")
    print("Press Ctrl+C to stop the worker")

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
