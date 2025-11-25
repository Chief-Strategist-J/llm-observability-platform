import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import asyncio

from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.orchestrator.activities.configurations_activity.mongodb_activity import (
    start_mongodb_activity,
    stop_mongodb_activity,
    restart_mongodb_activity,
    delete_mongodb_activity,
)
from infrastructure.orchestrator.activities.configurations_activity.kafka_activity import (
    start_kafka_activity,
    stop_kafka_activity,
    restart_kafka_activity,
    delete_kafka_activity,
)
from infrastructure.orchestrator.activities.configurations_activity.mongo_express_activity import (
    start_mongoexpress_activity,
    stop_mongoexpress_activity,
    restart_mongoexpress_activity,
    delete_mongoexpress_activity,
)

from infrastructure.orchestrator.workflows.kafka_mangodb_database_workflow import (
    KafkaMangoDBDatabaseWorkflow,
)

class KafkaMangoDBDatabaseWorker(BaseWorker):
    @property
    def workflows(self):
        return [KafkaMangoDBDatabaseWorkflow]

    @property
    def activities(self):
        return [
            start_kafka_activity,
            stop_kafka_activity,
            restart_kafka_activity,
            delete_kafka_activity,

            start_mongodb_activity,
            stop_mongodb_activity,
            restart_mongodb_activity,
            delete_mongodb_activity,

            start_mongoexpress_activity,
            stop_mongoexpress_activity,
            restart_mongoexpress_activity,
            delete_mongoexpress_activity,
        ]

async def main():
    
    worker = KafkaMangoDBDatabaseWorker(
        WorkerConfig(
            host="localhost",
            queue="kafka_mango_database-queue",
            port=7233,
            namespace="default",
            max_concurrency=None,
        )
    )

    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
