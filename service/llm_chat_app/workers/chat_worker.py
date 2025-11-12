import asyncio
import logging
import os
from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
class ChatWorker(BaseWorker):
    @property
    def workflows(self):
        from service.llm_chat_app.workflows.chat_setup_workflow import ChatSetupWorkflow
        from service.llm_chat_app.workflows.chat_cleanup_workflow import ChatCleanupWorkflow
        return [ChatSetupWorkflow, ChatCleanupWorkflow]
    @property
    def activities(self):
        from service.llm_chat_app.activities.chat_activity import (
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
    host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    queue = os.environ.get("TEMPORAL_TASK_QUEUE", "chat-service-queue")
    config = WorkerConfig(host=host, queue=queue)
    worker = ChatWorker(config=config)
    await worker.run()
if __name__ == "__main__":
    asyncio.run(main())
