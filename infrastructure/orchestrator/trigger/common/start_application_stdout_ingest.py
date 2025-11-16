#!/usr/bin/env python3

import asyncio
import logging
import sys
from pathlib import Path

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.base_pipeline import WorkflowConfig, PipelineExecutor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("logs_ingest_trigger")


class ApplicationStdoutIngestPipeline(PipelineExecutor):
    pass


async def main():
    config = WorkflowConfig(
        service_name="application-stdout-ingest",
        workflow_name="ApplicationStdoutIngestWorkflow",
        task_queue="logs-pipeline-queue",
        params={
            "service_name": "application-stdout-ingest",
            "search_paths": ["/var/log"],
            "include_patterns": ["*.log"],
            "labels": {
                "app": "application-stdout-ingest",
                "environment": "development"
            },
            "batch_size": 100,
            "flush_interval_seconds": 5,
            "host_loki_port": 31002
        }
    )
    pipeline = ApplicationStdoutIngestPipeline(config=config)
    await pipeline.run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())