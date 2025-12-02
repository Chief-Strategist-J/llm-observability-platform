# infrastructure/orchestrator/trigger/setup/start_inngest.py

import asyncio
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.base_pipeline import WorkflowConfig, PipelineExecutor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("service_setup")


class StartInngestPipeline(PipelineExecutor):
    pass

async def main():
    pipeline = StartInngestPipeline(
        config=WorkflowConfig(
            service_name="inngest",
            workflow_name="SetupInngestWorkflow",
            task_queue="service_setup_queue",
            params={
                "service_name": "inngest",
                "instance_id": 0
            }
        )
    )
    await pipeline.run_pipeline()
    logger.info("Inngest started successfully")


if __name__ == "__main__":
    asyncio.run(main())
