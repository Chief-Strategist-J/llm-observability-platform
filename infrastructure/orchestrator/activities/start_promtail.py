"""Temporal activity for managing Promtail container.

This module provides a Temporal activity to start the Promtail log shipping
container, which forwards logs to Loki as part of the monitoring
infrastructure. It handles container lifecycle management and ensures
Promtail is running and ready.

"""

import asyncio
import subprocess
import time

import docker
from temporalio import activity


class PromtailConfig:
    """Configuration for Promtail container management."""

    CONTAINER_NAME = "promtail"

    PROJECT_ROOT = "/home/j/live/dinesh/llm-chatbot-python"
    LOKI_DIR = f"{PROJECT_ROOT}/infrastructure/monitoring/component/loki"
    COMPOSE_FILE = f"{LOKI_DIR}/logger-loki-compose.yaml"

    CHECK_INTERVAL = 5
    MAX_WAIT_TIME = 60


@activity.defn
async def start_promtail() -> bool:
    """Start the Promtail log shipping container.

    This activity manages the lifecycle of starting the Promtail container,
    which is responsible for collecting logs from the host and shipping them
    to Loki. Since Promtail doesn't have a specific health endpoint, we
    verify it's running and wait for it to initialize.

    The activity uses the existing docker-compose configuration for the
    Promtail service, which runs as a log collection agent.

    Returns:
        bool: True if the Promtail container started successfully and is
             running.

    Raises:
        RuntimeError: If the container fails to start or isn't running after
                     the timeout.

    Example:
        >>> await start_promtail()
        True

    """
    activity.logger.info("Starting Promtail container")

    try:
        client = docker.from_env()
        container = await _get_or_start_promtail(client)
        return await _wait_for_running_promtail(container)

    except Exception as e:
        error_msg = f"Failed to start Promtail container: {e!s}"
        activity.logger.error(error_msg)
        raise RuntimeError(error_msg) from e


async def _get_or_start_promtail(client):
    """Get existing Promtail container or start a new one.

    Args:
        client: Docker client instance.

    Returns:
        Docker container object.
    """
    try:
        container = client.containers.get(PromtailConfig.CONTAINER_NAME)

        if container.status == "running":
            log_msg = (
                f"Container {PromtailConfig.CONTAINER_NAME} is already "
                "running"
            )
            activity.logger.info(log_msg)
            return container

        log_msg = (
            f"Starting existing container {PromtailConfig.CONTAINER_NAME}"
        )
        activity.logger.info(log_msg)
        container.start()

    except docker.errors.NotFound:
        log_msg = (
            f"Container {PromtailConfig.CONTAINER_NAME} not found, "
            "starting via docker-compose"
        )
        activity.logger.info(log_msg)
        await _start_promtail_via_compose()

    return client.containers.get(PromtailConfig.CONTAINER_NAME)


async def _start_promtail_via_compose() -> None:
    """Start the Promtail service using docker-compose.

    This helper function executes docker-compose up to start the Promtail
    service in detached mode. It uses the existing
    logger-loki-compose.yaml configuration and runs from the monitoring
    component directory.

    The function captures both stdout and stderr for proper logging and
    error handling in the Temporal activity context.

    Raises:
        RuntimeError: If docker-compose command fails or returns a non-zero
                     exit code.

    Note:
        This function assumes docker-compose is available in the system PATH
        and that the logger-loki-compose.yaml file exists in the monitoring
        component directory.

    """
    try:
        cmd = [
            "docker-compose",
            "-f",
            PromtailConfig.COMPOSE_FILE,
            "up",
            "-d",
            PromtailConfig.CONTAINER_NAME,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=PromtailConfig.LOKI_DIR,
        )

        activity.logger.info(f"Docker-compose output: {result.stdout}")
        if result.stderr:
            activity.logger.warning(
                f"Docker-compose warnings: {result.stderr}"
            )

    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Docker-compose failed: {e.stderr}")
        error_msg = f"Failed to start Promtail via docker-compose: {e}"
        raise RuntimeError(error_msg) from e


async def _wait_for_running_promtail(container) -> bool:
    """Wait for the Promtail container to be running and initialized.

    Since Promtail doesn't have a health endpoint, we simply wait for the
    container to be in a running state and allow time for it to initialize.
    Promtail is designed to be resilient and will automatically attempt to
    reconnect to Loki if needed.

    Args:
        container: Docker container object to monitor.

    Returns:
        bool: True when the Promtail container is running.

    Raises:
        RuntimeError: If the container isn't running after the timeout
                     period.

    """
    start_time = time.time()

    while time.time() - start_time < PromtailConfig.MAX_WAIT_TIME:
        try:
            container.reload()

            if container.status == "running":
                activity.logger.info("Promtail is running!")
                return True

        except Exception as e:
            activity.logger.warning(
                f"Promtail status check failed: {e!s}"
            )

        elapsed_time = time.time() - start_time
        log_msg = f"Waiting for Promtail to start... ({elapsed_time:.0f}s)"
        activity.logger.info(log_msg)
        await asyncio.sleep(PromtailConfig.CHECK_INTERVAL)

    error_msg = (
        f"Promtail did not start within {PromtailConfig.MAX_WAIT_TIME} "
        "seconds"
    )
    raise RuntimeError(error_msg)