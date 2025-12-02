# infrastructure/orchestrator/trigger/setup/start_prometheus.py

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


class StartPrometheusPipeline(PipelineExecutor):
    pass

async def main():
    pipeline = StartPrometheusPipeline(
        config=WorkflowConfig(
            service_name="prometheus",
            workflow_name="SetupPrometheusWorkflow",
            task_queue="service_setup_queue",
            params={
                "service_name": "prometheus",
                "instance_id": 0
            }
        )
    )
    await pipeline.run_pipeline()
    logger.info("Prometheus started successfully")


if __name__ == "__main__":
    asyncio.run(main())
