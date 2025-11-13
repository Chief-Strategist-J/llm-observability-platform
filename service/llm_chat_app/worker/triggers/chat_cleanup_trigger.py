import asyncio
import logging
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.base_pipeline import PipelineExecutor, WorkflowConfig
from service.llm_chat_app.worker.workflows.chat_cleanup_workflow import ChatCleanupWorkflow  # noqa

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def main():
    config = WorkflowConfig(
        service_name="chat-cleanup",
        workflow_name="ChatCleanupWorkflow",
        task_queue=os.environ.get("TEMPORAL_TASK_QUEUE", "chat-service-queue"),
        temporal_host=os.environ.get("TEMPORAL_HOST", "localhost:7233"),
        params={"service_name": "chat-cleanup"},
    )
    pipeline = PipelineExecutor(config=config)
    logger.info("trigger chat-cleanup starting")
    await pipeline.run_pipeline()
    logger.info("trigger chat-cleanup finished")

if __name__ == "__main__":
    asyncio.run(main())
