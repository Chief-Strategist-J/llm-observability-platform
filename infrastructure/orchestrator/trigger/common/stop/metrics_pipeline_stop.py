#!/usr/bin/env python3
"""Stop script for Metrics Pipeline - terminates workflow, stops containers, and cleans up volumes."""

import asyncio
import logging
from pathlib import Path
import sys

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

import docker
from temporalio.client import Client, WorkflowFailureError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TEMPORAL_HOST = "localhost:7233"
CONTAINER_NAMES = ["prometheus-development", "grafana-development"]
VOLUME_NAMES = [
    "prometheus-data",
    "prometheus-config",
    "grafana-data",
]


async def stop_workflow(workflow_id: str) -> bool:
    """
    Stop the Temporal workflow.
    """
    try:
        logger.info(f"Connecting to Temporal server at {TEMPORAL_HOST}")
        client = await Client.connect(TEMPORAL_HOST)

        logger.info(f"Terminating workflow: {workflow_id}")
        handle = client.get_workflow_handle(workflow_id)
        await handle.terminate(reason="Manual stop requested")
        logger.info("✅ Workflow terminated successfully")
        return True
    except WorkflowFailureError as e:
        logger.warning(f"Workflow already terminated or not found: {e}")
        return True
    except Exception as e:
        logger.error(f"Failed to stop workflow: {e}")
        return False


def stop_containers() -> bool:
    """
    Stop and remove all pipeline containers.
    """
    try:
        client = docker.from_env()
        logger.info("Stopping and removing containers...")

        for container_name in CONTAINER_NAMES:
            try:
                container = client.containers.get(container_name)
                logger.info(f"Stopping container: {container_name}")
                container.stop(timeout=10)
                logger.info(f"Removing container: {container_name}")
                container.remove(force=True)
                logger.info(f"✅ Container {container_name} stopped and removed")
            except docker.errors.NotFound:
                logger.info(f"Container {container_name} not found, skipping")
            except Exception as e:
                logger.error(f"Failed to stop container {container_name}: {e}")

        logger.info("✅ All containers stopped and removed")
        return True
    except Exception as e:
        logger.error(f"Failed to stop containers: {e}")
        return False


def remove_volumes() -> bool:
    """
    Remove all pipeline volumes.
    """
    try:
        client = docker.from_env()
        logger.info("Removing volumes...")

        for volume_name in VOLUME_NAMES:
            try:
                volume = client.volumes.get(volume_name)
                logger.info(f"Removing volume: {volume_name}")
                volume.remove(force=True)
                logger.info(f"✅ Volume {volume_name} removed")
            except docker.errors.NotFound:
                logger.info(f"Volume {volume_name} not found, skipping")
            except Exception as e:
                logger.error(f"Failed to remove volume {volume_name}: {e}")

        logger.info("✅ All volumes removed")
        return True
    except Exception as e:
        logger.error(f"Failed to remove volumes: {e}")
        return False


async def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python3 metrics_pipeline_stop.py <workflow_id>")
        sys.exit(1)

    workflow_id = sys.argv[1]

    logger.info("=" * 80)
    logger.info("Stopping Metrics Pipeline (Grafana + Prometheus)...")
    logger.info(f"Workflow ID: {workflow_id}")
    logger.info("=" * 80)

    # Stop workflow
    workflow_stopped = await stop_workflow(workflow_id)

    # Stop containers
    containers_stopped = stop_containers()

    # Remove volumes
    volumes_removed = remove_volumes()

    logger.info("=" * 80)
    if workflow_stopped and containers_stopped and volumes_removed:
        logger.info("✅ Metrics Pipeline stopped and cleaned up successfully!")
    else:
        logger.warning(
            "⚠️ Metrics Pipeline stopped with some warnings. Check logs above."
        )
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
