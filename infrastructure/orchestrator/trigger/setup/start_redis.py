# infrastructure/orchestrator/trigger/setup/start_redis.py

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


class StartRedisPipeline(PipelineExecutor):
    pass


async def main():
    pipeline = StartRedisPipeline(
        config=WorkflowConfig(
            service_name="redis",
            workflow_name="SetupRedisWorkflow",
            task_queue="service_setup_queue",
            params={
                "service_name": "redis",
                "instance_id": 0
            }
        )
    )
    
    await pipeline.run_pipeline()
    logger.info("Redis infrastructure started successfully")


if __name__ == "__main__":
    asyncio.run(main())
