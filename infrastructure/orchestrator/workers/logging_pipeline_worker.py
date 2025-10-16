"""Logging Pipeline Worker Module.

This module provides a Temporal worker for the logging pipeline system. It connects to a
Temporal server and runs workflows and activities related to logging pipeline
operations, specifically handling container startup tasks.

"""

import asyncio
from pathlib import Path
import sys

# Add the project root to sys.path when running as a script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from temporalio.client import Client
from temporalio.worker import Worker

from infrastructure.orchestrator.activities import start_app_container
from infrastructure.orchestrator.workflows.logging_pipeline_workflow import (
    LoggingPipelineWorkflow,
)


async def main() -> None:
    """Main entry point for the logging pipeline worker.

    Connects to the Temporal server at localhost:7233 and starts a worker that processes
    logging pipeline tasks. The worker handles the LoggingPipelineWorkflow and
    start_app_container activity.

    The worker runs indefinitely until manually stopped, processing tasks from the
    'logging-pipeline' task queue.

    """
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="logging-pipeline",
        workflows=[LoggingPipelineWorkflow],
        activities=[start_app_container],
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
