#!/usr/bin/env python3

import asyncio
import logging
import sys
from pathlib import Path

from base.base_pipeline import WorkflowConfig, PipelineExecutor

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("database_pipeline_trigger")


class DatabasePipeline(PipelineExecutor):
    pass


async def main():
    config = WorkflowConfig(
        service_name="database-pipeline",
        workflow_name="DatabasePipelineWorkflow",
        task_queue="database-pipeline-queue",
    )
    pipeline = DatabasePipeline(config=config)
    await pipeline.run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
