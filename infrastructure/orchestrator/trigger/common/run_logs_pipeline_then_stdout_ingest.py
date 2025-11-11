#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.base_pipeline import WorkflowConfig, ChainedPipelineExecutor



async def main():
    first = WorkflowConfig(
        service_name="logs-pipeline",
        workflow_name="LogsPipelineWorkflow",
        task_queue="logs-pipeline-queue",
        params={"service_name": "logs-pipeline"}
    )

    second = WorkflowConfig(
        service_name="application-stdout-ingest",
        workflow_name="ApplicationStdoutIngestWorkflow",
        task_queue="logs-pipeline-queue",
        params={
            "service_name": "application-stdout-ingest",
            "search_paths": ["/var/log"],
            "include_patterns": ["*.log"],
            "labels": {"app": "application-stdout-ingest", "environment": "development"},
            "batch_size": 100,
            "flush_interval_seconds": 5,
            "host_loki_port": 31002
        }
    )

    executor = ChainedPipelineExecutor([first, second])
    result = await executor.run()
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
