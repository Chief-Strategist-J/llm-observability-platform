#!/usr/bin/env python3
"""
Simple trigger script to start Tracing Pipeline using Temporal workflows.
"""

import asyncio
import logging
import os
from pathlib import Path
import sys
import time

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from temporalio.client import Client


class WorkflowConfig:
    DEFAULT_SERVICE_NAME = "tracing-pipeline"
    DEFAULT_WORKFLOW_NAME = "TracingPipelineWorkflow"
    DEFAULT_TASK_QUEUE = "tracing-pipeline-queue"
    DEFAULT_TEMPORAL_HOST = "localhost:7233"
    DEFAULT_WEB_UI_URL = "http://localhost:8080"

    def __init__(
        self,
        service_name: str | None = None,
        workflow_name: str | None = None,
        task_queue: str | None = None,
        temporal_host: str | None = None,
        web_ui_url: str | None = None,
    ):
        self.service_name = service_name or os.getenv(
            "TEMPORAL_SERVICE_NAME", self.DEFAULT_SERVICE_NAME
        )
        self.workflow_name = workflow_name or os.getenv(
            "TEMPORAL_WORKFLOW_NAME", self.DEFAULT_WORKFLOW_NAME
        )
        self.task_queue = task_queue or os.getenv(
            "TEMPORAL_TASK_QUEUE", self.DEFAULT_TASK_QUEUE
        )
        self.temporal_host = temporal_host or os.getenv(
            "TEMPORAL_HOST", self.DEFAULT_TEMPORAL_HOST
        )
        self.web_ui_url = web_ui_url or os.getenv(
            "TEMPORAL_WEB_UI_URL", self.DEFAULT_WEB_UI_URL
        )


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def start_tracing_pipeline(config: WorkflowConfig) -> str | None:
    try:
        logger.info(f"Connecting to Temporal server at {config.temporal_host}")
        client = await Client.connect(config.temporal_host)

        workflow_id = f"{config.service_name.replace('-', '_')}_{int(time.time())}"

        result = await client.start_workflow(
            config.workflow_name,
            config.service_name,
            id=workflow_id,
            task_queue=config.task_queue,
        )

        logger.info("Tracing Pipeline workflow started successfully!")
        logger.info(f"Workflow ID: {result.id}")
        logger.info(f"Check {config.web_ui_url} to monitor progress")
        return result.id

    except Exception as e:
        logger.error(f"Failed to start {config.service_name} workflow: {e}")
        return None


def parse_arguments() -> WorkflowConfig:
    config = WorkflowConfig()

    if len(sys.argv) > 1:
        config.service_name = sys.argv[1]

    if len(sys.argv) > 2:
        config.workflow_name = sys.argv[2]

    if len(sys.argv) > 3:
        config.task_queue = sys.argv[3]

    return config


async def main():
    logger.info("Starting Tracing Pipeline (Grafana + Jaeger)...")
    logger.info("=" * 80)

    config = parse_arguments()

    logger.info(f"Service: {config.service_name}")
    logger.info(f"Workflow: {config.workflow_name}")
    logger.info(f"Task Queue: {config.task_queue}")
    logger.info(f"Temporal Host: {config.temporal_host}")
    logger.info(f"Web UI: {config.web_ui_url}")
    logger.info("=" * 80)

    workflow_id = await start_tracing_pipeline(config)

    if workflow_id:
        logger.info("=" * 80)
        logger.info("✅ Tracing Pipeline workflow started successfully!")
        logger.info(f"📋 Workflow ID: {workflow_id}")
        logger.info("")
        logger.info("🔗 Service URLs:")
        logger.info("   Grafana:    http://localhost:31001 (admin/SuperSecret123!)")
        logger.info("   Jaeger UI:  http://localhost:16686")
        logger.info("   OTLP gRPC:  localhost:4317")
        logger.info("   OTLP HTTP:  localhost:4318")
        logger.info("")
        logger.info("🛑 To stop this workflow:")
        logger.info(f"   python3 trigger/tracing_pipeline/stop.py {workflow_id}")
        logger.info("=" * 80)
    else:
        logger.error("=" * 80)
        logger.error("❌ Failed to start Tracing Pipeline workflow")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
