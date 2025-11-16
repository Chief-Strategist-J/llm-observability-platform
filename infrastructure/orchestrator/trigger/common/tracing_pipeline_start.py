#\!/usr/bin/env python3

import asyncio
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.base_pipeline import WorkflowConfig, PipelineExecutor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("tracing_pipeline_trigger")


class TracingPipeline(PipelineExecutor):
    pass


async def main():
    config = WorkflowConfig(
        service_name="tracing-pipeline",
        workflow_name="TracingPipelineWorkflow",
        task_queue="tracing-pipeline-queue",
        params={
            "service_name": "tracing-pipeline"
        }
    )
    pipeline = TracingPipeline(config=config)
    await pipeline.run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
