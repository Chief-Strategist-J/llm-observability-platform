import asyncio
import logging
import os
import sys
from pathlib import Path

from infrastructure.orchestrator.base.base_pipeline import PipelineExecutor, WorkflowConfig
from service.llm_chat_app.worker.workflows.flyio_deploy_workflow import FlyioDeploymentWorkflow

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("flyio_deploy_trigger")


def create_config() -> WorkflowConfig:
    return WorkflowConfig(
        service_name="flyio-deploy",
        workflow_name=FlyioDeploymentWorkflow.__name__,
        task_queue=os.environ.get("TEMPORAL_TASK_QUEUE", "chat-service-queue"),
        temporal_host=os.environ.get("TEMPORAL_HOST", "localhost:7233"),
        params={"service_name": "flyio-deploy"},
    )


async def main():
    config = create_config()
    pipeline = PipelineExecutor(config=config)
    logger.info("trigger flyio-deploy starting")
    await pipeline.run_pipeline()
    logger.info("trigger flyio-deploy finished")


if __name__ == "__main__":
    asyncio.run(main())
