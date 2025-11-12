import asyncio
import logging
import os

from infrastructure.orchestrator.base.base_pipeline import (
    PipelineExecutor,
    WorkflowConfig,
)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def main():
    config = WorkflowConfig(service_name="chat-cleanup", workflow_name="ChatCleanupWorkflow", task_queue=os.environ.get("TEMPORAL_TASK_QUEUE", "chat-service-queue"), temporal_host=os.environ.get("TEMPORAL_HOST", "localhost:7233"), params={"service_name": "chat-cleanup"})
    pipeline = PipelineExecutor(config=config)
    logger.info("trigger chat-cleanup starting")
    await pipeline.run_pipeline()
    logger.info("trigger chat-cleanup finished")

if __name__ == "__main__":
    asyncio.run(main())
