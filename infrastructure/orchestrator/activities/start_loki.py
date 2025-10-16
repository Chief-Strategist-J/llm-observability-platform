"""Temporal activity for managing Loki container.

This module provides a Temporal activity to start the Loki logging service
container, which is part of the monitoring infrastructure. It handles
container lifecycle management and health checking to ensure Loki is ready
to receive logs.

"""

import asyncio
import subprocess
import time
import urllib.request

import docker
from temporalio import activity


class LokiConfig:
    """Configuration for Loki container management."""

    CONTAINER_NAME = "loki"
    PORT = 3100

    PROJECT_ROOT = "/home/j/live/dinesh/llm-chatbot-python"
    LOKI_DIR = f"{PROJECT_ROOT}/infrastructure/monitoring/component/loki"
    COMPOSE_FILE = f"{LOKI_DIR}/logger-loki-compose.yaml"

    HEALTH_ENDPOINT = f"http://localhost:{PORT}/ready"
    REQUEST_TIMEOUT = 5
    CHECK_INTERVAL = 10
    MAX_WAIT_TIME = 300

    HTTP_OK = 200


@activity.defn
async def start_loki() -> bool:
    """Start the Loki logging container and wait until it is healthy.

    This activity manages the complete lifecycle of starting the Loki
    container, including checking if it already exists, starting it if
    needed, and waiting for the health endpoint to respond successfully.

    The activity uses the existing docker-compose configuration for the
    Loki service, which runs on port 3100 and provides a /ready endpoint
    for health checking.

    Returns:
        bool: True if the Loki container started successfully and is
             healthy.

    Raises:
        RuntimeError: If the container fails to start within the timeout
                     period or if the health check fails.

    Example:
        >>> await start_loki()
        True

    """
    activity.logger.info("Starting Loki container")

    try:
        client = docker.from_env()
        container = await _get_or_start_loki(client)
        return await _wait_for_healthy_loki(container)

    except Exception as e:
        error_msg = f"Failed to start Loki container: {e!s}"
        activity.logger.error(error_msg)
        raise RuntimeError(error_msg) from e


async def _get_or_start_loki(client):
    """Get existing Loki container or start a new one.

    Args:
        client: Docker client instance.

    Returns:
        Docker container object.
    """
    try:
        container = client.containers.get(LokiConfig.CONTAINER_NAME)

        if container.status == "running":
            activity.logger.info(
                f"Container {LokiConfig.CONTAINER_NAME} is already running"
            )
            return container

        log_msg = f"Starting existing container {LokiConfig.CONTAINER_NAME}"
        activity.logger.info(log_msg)
        container.start()

    except docker.errors.NotFound:
        log_msg = (
            f"Container {LokiConfig.CONTAINER_NAME} not found, starting "
            "via docker-compose"
        )
        activity.logger.info(log_msg)
        await _start_loki_via_compose()

    return client.containers.get(LokiConfig.CONTAINER_NAME)


async def _start_loki_via_compose() -> None:
    """Start the Loki service using docker-compose.

    This helper function executes docker-compose up to start the Loki
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
            LokiConfig.COMPOSE_FILE,
            "up",
            "-d",
            LokiConfig.CONTAINER_NAME,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=LokiConfig.LOKI_DIR,
        )

        activity.logger.info(f"Docker-compose output: {result.stdout}")
        if result.stderr:
            activity.logger.warning(
                f"Docker-compose warnings: {result.stderr}"
            )

    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Docker-compose failed: {e.stderr}")
        error_msg = f"Failed to start Loki via docker-compose: {e}"
        raise RuntimeError(error_msg) from e


async def _wait_for_healthy_loki(container) -> bool:
    """Wait for the Loki container to become healthy.

    This function implements a polling mechanism to wait for Loki to become
    ready. It checks the container status and performs HTTP requests to the
    /ready endpoint until Loki responds successfully.

    Args:
        container: Docker container object to monitor for health.

    Returns:
        bool: True when the Loki health check passes.

    Raises:
        RuntimeError: If the container doesn't become healthy within the
                     timeout period or if the container status becomes
                     non-running.

    """
    start_time = time.time()

    while time.time() - start_time < LokiConfig.MAX_WAIT_TIME:
        try:
            container.reload()

            if container.status != "running":
                error_msg = (
                    f"Container is not running. Status: "
                    f"{container.status}"
                )
                raise RuntimeError(error_msg)

            try:
                with urllib.request.urlopen(
                    LokiConfig.HEALTH_ENDPOINT,
                    timeout=LokiConfig.REQUEST_TIMEOUT,
                ) as response:
                    if response.status == LokiConfig.HTTP_OK:
                        activity.logger.info("Loki is healthy!")
                        return True
            except (urllib.error.URLError, OSError):
                pass

        except Exception as e:
            activity.logger.warning(f"Loki health check failed: {e!s}")

        elapsed_time = time.time() - start_time
        log_msg = (
            f"Waiting for Loki to become healthy... ({elapsed_time:.0f}s)"
        )
        activity.logger.info(log_msg)
        await asyncio.sleep(LokiConfig.CHECK_INTERVAL)

    error_msg = (
        f"Loki did not become healthy within {LokiConfig.MAX_WAIT_TIME} "
        "seconds"
    )
    raise RuntimeError(error_msg)