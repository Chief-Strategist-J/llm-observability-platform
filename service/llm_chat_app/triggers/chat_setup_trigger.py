import asyncio
import os
from infrastructure.orchestrator.base.base_pipeline import WorkflowConfig, PipelineExecutor
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
async def main():
    config = WorkflowConfig(service_name="chat-setup", workflow_name="ChatSetupWorkflow", task_queue=os.environ.get("TEMPORAL_TASK_QUEUE", "chat-service-queue"), temporal_host=os.environ.get("TEMPORAL_HOST", "localhost:7233"), params={"service_name": "chat-setup"})
    pipeline = PipelineExecutor(config=config)
    logger.info("trigger chat-setup starting")
    await pipeline.run_pipeline()
    logger.info("trigger chat-setup finished")
if __name__ == "__main__":
    asyncio.run(main())
