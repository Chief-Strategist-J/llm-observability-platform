"""Database Pipeline Worker Module.

This module provides a Temporal worker for the database pipeline system. It connects to
a Temporal server and runs workflows and activities related to database pipeline
operations, specifically handling Neo4j and Qdrant container startup tasks.

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

from infrastructure.orchestrator.activities.database_activity.neo4j_activity import (
    start_neo4j_container,
)
from infrastructure.orchestrator.activities.database_activity.qdrant_activity import (
    start_qdrant_container,
)
from infrastructure.orchestrator.workflows.database_pipeline_workflow import (
    DatabasePipelineWorkflow,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point for the database pipeline worker.

    Connects to the Temporal server at localhost:7233 and starts a worker that processes
    database pipeline tasks. The worker handles the DatabasePipelineWorkflow and all
    database-related activities (Neo4j, Qdrant).

    The worker runs indefinitely until manually stopped, processing tasks from the
    'database-pipeline-queue' task queue.

    """
    client = None
    worker = None

    try:
        logger.info("Attempting to connect to Temporal server at localhost:7233")
        client = await Client.connect("localhost:7233")
        logger.info("Successfully connected to Temporal server")

        logger.info("Initializing Database Pipeline Worker")
        worker = Worker(
            client,
            task_queue="database-pipeline-queue",
            workflows=[DatabasePipelineWorkflow],
            activities=[
                start_neo4j_container,
                start_qdrant_container,
            ],
        )

        logger.info(
            "Database Pipeline Worker started. Task Queue: database-pipeline-queue"
        )
        logger.info("Listening for workflows: DatabasePipelineWorkflow")
        logger.info(
            "Available activities: start_neo4j_container, start_qdrant_container"
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
            logger.info("Stopping Database Pipeline Worker")
        if client:
            logger.info("Closing Temporal client connection")
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
