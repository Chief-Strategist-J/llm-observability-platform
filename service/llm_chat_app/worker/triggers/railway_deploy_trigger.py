import asyncio
import logging
import os
import sys
from pathlib import Path

from infrastructure.orchestrator.base.base_pipeline import PipelineExecutor, WorkflowConfig
from service.llm_chat_app.worker.workflows.railway_deploy_workflow import RailwayDeploymentWorkflow

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("railway_deploy_trigger")


def create_config() -> WorkflowConfig:
    return WorkflowConfig(
        service_name="railway-deploy",
        workflow_name=RailwayDeploymentWorkflow.__name__,
        task_queue=os.environ.get("TEMPORAL_TASK_QUEUE", "chat-service-queue"),
        temporal_host=os.environ.get("TEMPORAL_HOST", "localhost:7233"),
        params={"service_name": "railway-deploy"},
    )


async def main():
    config = create_config()
    pipeline = PipelineExecutor(config=config)
    logger.info("trigger railway-deploy starting")
    await pipeline.run_pipeline()
    logger.info("trigger railway-deploy finished")


if __name__ == "__main__":
    asyncio.run(main())
