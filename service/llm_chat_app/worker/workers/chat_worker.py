import asyncio
import logging
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Sequence, Type

CURRENT = Path(__file__).resolve()
PROJECT_ROOT = CURRENT.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

FULL_ROOT = CURRENT.parents[4]
if str(FULL_ROOT) not in sys.path:
    sys.path.insert(0, str(FULL_ROOT))

from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from worker.workflows.chat_setup_workflow import ChatSetupWorkflow
from worker.workflows.chat_cleanup_workflow import ChatCleanupWorkflow
from worker.activities.chat_activity import (
    build_chat_image_activity,
    run_chat_container_activity,
    stop_chat_container_activity,
    delete_chat_container_activity,
    delete_chat_image_activity,
    start_neo4j_dependency_activity,
    stop_neo4j_dependency_activity,
    delete_neo4j_dependency_activity,
    verify_cloudflare_dependency_activity,
    check_chat_health_activity,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ChatWorker")


@dataclass(frozen=True)
class ChatWorkerConfig(WorkerConfig):
    host: str = "localhost"
    queue: str = "chat-service-queue"
    port: int = 7233
    namespace: str = "default"


class ChatWorker(BaseWorker):
    def __init__(self, config: ChatWorkerConfig = None):
        if config is None:
            config = ChatWorkerConfig()
        super().__init__(config)

    @property
    def workflows(self) -> Sequence[Type]:
        return [ChatSetupWorkflow, ChatCleanupWorkflow]

    @property
    def activities(self) -> Sequence[object]:
        return [
            build_chat_image_activity,
            run_chat_container_activity,
            stop_chat_container_activity,
            delete_chat_container_activity,
            delete_chat_image_activity,
            start_neo4j_dependency_activity,
            stop_neo4j_dependency_activity,
            delete_neo4j_dependency_activity,
            verify_cloudflare_dependency_activity,
            check_chat_health_activity,
        ]


async def main():
    worker = ChatWorker()
    logger.info("ChatWorker starting...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
