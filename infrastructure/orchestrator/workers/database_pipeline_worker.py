import asyncio
from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig

from infrastructure.orchestrator.activities.configurations_activity.neo4j_activity import (
    start_neo4j_activity, stop_neo4j_activity,
    restart_neo4j_activity, delete_neo4j_activity,
)
from infrastructure.orchestrator.activities.configurations_activity.qdrant_activity import (
    start_qdrant_activity, stop_qdrant_activity,
    restart_qdrant_activity, delete_qdrant_activity,
)
from infrastructure.orchestrator.workflows.database_workflow import (
    DatabaseWorkflow,
)


class DatabasePipelineWorker(BaseWorker):
    @property
    def workflows(self):
        return [DatabasePipelineWorkflow]

    @property
    def activities(self):
        return [
            start_neo4j_activity,
            stop_neo4j_activity,
            restart_neo4j_activity,
            delete_neo4j_activity,
            start_qdrant_activity,
            stop_qdrant_activity,
            restart_qdrant_activity,
            delete_qdrant_activity,
        ]


async def main():
    worker = DatabasePipelineWorker(
        WorkerConfig(
            host="localhost",
            queue="database-pipeline-queue",
            port=7233,
            namespace="default",
            max_concurrency=None,
        )
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
