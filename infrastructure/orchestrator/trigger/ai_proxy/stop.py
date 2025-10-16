#!/usr/bin/env python3
"""Modular trigger script to stop services using Temporal workflows.

This script provides a configurable way to stop any service workflow that was started
using the corresponding start trigger script. It can terminate workflows by ID.

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

    # Default configuration
    DEFAULT_TEMPORAL_HOST = "localhost:7233"
    DEFAULT_WEB_UI_URL = "http://localhost:8080"
    DEFAULT_STOP_REASON = "Manual stop requested via trigger script"

    def __init__(
        self,
        temporal_host: str | None = None,
        web_ui_url: str | None = None,
        stop_reason: str | None = None,
    ):
        """
        Initialize workflow configuration with optional overrides.
        """
        self.temporal_host = temporal_host or os.getenv(
            "TEMPORAL_HOST", self.DEFAULT_TEMPORAL_HOST
        )
        self.web_ui_url = web_ui_url or os.getenv(
            "TEMPORAL_WEB_UI_URL", self.DEFAULT_WEB_UI_URL
        )
        self.stop_reason = stop_reason or os.getenv(
            "TEMPORAL_STOP_REASON", self.DEFAULT_STOP_REASON
        )


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def stop_service_workflow(workflow_id: str, config: WorkflowConfig) -> bool:
    """Stop a service workflow with the given configuration.

    Args:
        workflow_id: The workflow ID to terminate
        config: WorkflowConfig object containing configuration

    Returns:
        bool: True if workflow was terminated successfully

    """
    try:
        # Connect to Temporal server
        logger.info(f"Connecting to Temporal server at {config.temporal_host}")
        client = await Client.connect(config.temporal_host)

        # Get the workflow handle
        logger.info(f"Getting workflow handle for ID: {workflow_id}")
        handle = client.get_workflow_handle(workflow_id)

        # Terminate the workflow
        logger.info(f"Terminating workflow '{workflow_id}'")
        logger.info(f"Reason: {config.stop_reason}")

        await handle.terminate(config.stop_reason)

        logger.info("Successfully terminated workflow!")
        logger.info(f"Check {config.web_ui_url} for confirmation")

        return True

    except Exception as e:
        logger.error(f"Failed to terminate workflow '{workflow_id}': {e}")
        return False


def parse_arguments() -> tuple[str, WorkflowConfig]:
    """Parse command line arguments and return workflow ID and configuration.

    Returns:
        tuple: (workflow_id, config) where config is WorkflowConfig object

    """
    # Check if workflow ID was provided
    if len(sys.argv) < 2:
        logger.error(
            "Usage: python3 trigger/ai_proxy/stop.py <workflow_id> [stop_reason]"
        )
        logger.info(
            "Example: python3 trigger/ai_proxy/stop.py ai_proxy_service_1699123400"
        )
        logger.info(
            "Optional: python3 trigger/ai_proxy/stop.py ai_proxy_service_1699123400 'Emergency stop'"
        )
        logger.info(
            "Get the workflow ID from the start script output or Temporal Web UI"
        )
        sys.exit(1)

    workflow_id = sys.argv[1]

    # Default configuration
    config = WorkflowConfig()

    # Optional stop reason
    if len(sys.argv) > 2:
        config.stop_reason = sys.argv[2]

    return workflow_id, config


async def main():
    """
    Main entry point for the stop trigger script.
    """
    logger.info("Stopping service workflow via Temporal...")
    logger.info("=" * 60)

    # Parse workflow ID and configuration from arguments
    workflow_id, config = parse_arguments()

    # Log configuration being used
    logger.info("Using configuration:")
    logger.info(f"  Workflow ID: {workflow_id}")
    logger.info(f"  Temporal Host: {config.temporal_host}")
    logger.info(f"  Web UI: {config.web_ui_url}")
    logger.info(f"  Stop Reason: {config.stop_reason}")
    logger.info("=" * 60)

    success = await stop_service_workflow(workflow_id, config)

    if success:
        logger.info("=" * 60)
        logger.info("✅ Workflow terminated successfully!")
        logger.info("📋 The service container should now be stopped")
    else:
        logger.error("=" * 60)
        logger.error("❌ Failed to terminate workflow")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
