#!/usr/bin/env python3
"""Modular trigger script to start services using Temporal workflows.

This script provides a configurable way to start any service using Temporal workflows.
It can be easily adapted for different services by changing the configuration.

"""

import asyncio
import logging
import os
from pathlib import Path
import sys

# Add the project root to sys.path when running as a script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from temporalio.client import Client


class WorkflowConfig:
    """
    Configuration for workflow execution.
    """

    # Default configuration for ai-proxy-service
    DEFAULT_SERVICE_NAME = "ai-proxy-service"
    DEFAULT_WORKFLOW_NAME = "LoggingPipelineWorkflow"
    DEFAULT_TASK_QUEUE = "logging-pipeline"
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
        """
        Initialize workflow configuration with optional overrides.
        """
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


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def start_service_workflow(config: WorkflowConfig) -> str | None:
    """Start a service workflow with the given configuration.

    Args:
        config: WorkflowConfig object containing all configuration

    Returns:
        str: Workflow ID if successful, None if failed

    """
    try:
        # Connect to Temporal server
        logger.info(f"Connecting to Temporal server at {config.temporal_host}")
        client = await Client.connect(config.temporal_host)

        # Generate unique workflow ID
        import time

        workflow_id = f"{config.service_name.replace('-', '_')}-{int(time.time())}"

        # Start the workflow
        logger.info(f"Starting workflow: {config.workflow_name}")
        logger.info(f"Service: {config.service_name}")
        logger.info(f"Task Queue: {config.task_queue}")

        result = await client.start_workflow(
            config.workflow_name,
            config.service_name,
            id=workflow_id,
            task_queue=config.task_queue,
        )

        logger.info("Successfully started service workflow!")
        logger.info(f"Workflow ID: {result.id}")
        logger.info(f"Check {config.web_ui_url} to monitor progress")

        return result.id

    except Exception as e:
        logger.error(f"Failed to start {config.service_name} workflow: {e}")
        return None


def parse_arguments() -> WorkflowConfig:
    """Parse command line arguments and return configuration.

    Returns:
        WorkflowConfig: Configuration object with parsed arguments

    """
    # Default configuration
    config = WorkflowConfig()

    # Parse command line arguments
    if len(sys.argv) > 1:
        config.service_name = sys.argv[1]

    if len(sys.argv) > 2:
        config.workflow_name = sys.argv[2]

    if len(sys.argv) > 3:
        config.task_queue = sys.argv[3]

    return config


async def main():
    """
    Main entry point for the trigger script.
    """
    logger.info("Starting service via Temporal workflow...")
    logger.info("=" * 60)

    # Parse configuration from arguments or environment
    config = parse_arguments()

    # Log configuration being used
    logger.info("Using configuration:")
    logger.info(f"  Service: {config.service_name}")
    logger.info(f"  Workflow: {config.workflow_name}")
    logger.info(f"  Task Queue: {config.task_queue}")
    logger.info(f"  Temporal Host: {config.temporal_host}")
    logger.info(f"  Web UI: {config.web_ui_url}")
    logger.info("=" * 60)

    workflow_id = await start_service_workflow(config)

    if workflow_id:
        logger.info("=" * 60)
        logger.info("✅ Workflow started successfully!")
        logger.info(f"📋 Workflow ID: {workflow_id}")
        logger.info("🔗 To stop this workflow later, use:")
        logger.info(f"   python3 trigger/ai_proxy/stop.py {workflow_id}")
    else:
        logger.error("=" * 60)
        logger.error("❌ Failed to start workflow")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
