"""Database Pipeline Worker Module.

This module provides a Temporal worker for the database pipeline system. It connects to
a Temporal server and runs workflows and activities related to database pipeline
operations, specifically handling Neo4j and Qdrant container startup tasks.

"""

import asyncio
from pathlib import Path
import sys

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from temporalio.client import Client
from temporalio.worker import Worker

from infrastructure.orchestrator.activities.database_activity.neo4j_activity import (
    start_neo4j_container,
)
from infrastructure.orchestrator.activities.database_activity.qdrant_activity import (
    start_qdrant_container,
)
from infrastructure.orchestrator.workflows.database_pipeline_workflow import (
    DatabasePipelineWorkflow,
)


async def main() -> None:
    """Main entry point for the database pipeline worker.

    Connects to the Temporal server at localhost:7233 and starts a worker that processes
    database pipeline tasks. The worker handles the DatabasePipelineWorkflow and all
    database-related activities (Neo4j, Qdrant).

    The worker runs indefinitely until manually stopped, processing tasks from the
    'database-pipeline-queue' task queue.

    """
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="database-pipeline-queue",
        workflows=[DatabasePipelineWorkflow],
        activities=[
            start_neo4j_container,
            start_qdrant_container,
        ],
    )

    print("Database Pipeline Worker started. Task Queue: database-pipeline-queue")
    print("Listening for workflows: DatabasePipelineWorkflow")
    print("Press Ctrl+C to stop the worker")

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
