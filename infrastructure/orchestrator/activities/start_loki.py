"""Temporal activity for managing Loki container.

This module provides a Temporal activity to start the Loki logging service container,
which is part of the monitoring infrastructure. It handles container lifecycle
management and health checking to ensure Loki is ready to receive logs.

"""

from temporalio import activity


@activity.defn
async def start_loki() -> bool:
    """Start the Loki logging container and wait until it is healthy.

    This activity manages the complete lifecycle of starting the Loki container,
    including checking if it already exists, starting it if needed, and waiting
    for the health endpoint to respond successfully.

    The activity uses the existing docker-compose configuration for the Loki service,
    which runs on port 3100 and provides a /ready endpoint for health checking.

    Returns:
        bool: True if the Loki container started successfully and is healthy.

    Raises:
        Exception: If the container fails to start within the timeout period
                  or if the health check fails.

    Example:
        >>> await start_loki()
        True

    """
    activity.logger.info("Starting Loki container")

    import docker

    try:
        client = docker.from_env()

        container_name = "loki"
        try:
            container = client.containers.get(container_name)
            if container.status == "running":
                activity.logger.info(f"Container {container_name} is already running")
                return await _wait_for_healthy_loki(container)
            activity.logger.info(f"Starting existing container {container_name}")
            container.start()
        except docker.errors.NotFound:
            activity.logger.info(
                f"Container {container_name} not found, " f"starting via docker-compose"
            )
            await _start_loki_via_compose()

        container = client.containers.get(container_name)
        return await _wait_for_healthy_loki(container)

    except Exception as e:
        activity.logger.error(f"Failed to start Loki container: {e!s}")
        raise


async def _start_loki_via_compose() -> None:
    """Start the Loki service using docker-compose.

    This helper function executes docker-compose up to start the Loki service
    in detached mode. It uses the existing logger-loki-compose.yaml configuration
    and runs from the monitoring component directory.

    The function captures both stdout and stderr for proper logging and error
    handling in the Temporal activity context.

    Raises:
        Exception: If docker-compose command fails or returns a non-zero exit code.

    Note:
        This function assumes docker-compose is available in the system PATH
        and that the logger-loki-compose.yaml file exists in the monitoring component directory.

    """
    import subprocess

    try:
        cmd = [
            "docker-compose",
            "-f",
            "/home/j/live/dinesh/llm-chatbot-python/infrastructure/monitoring/component/loki/logger-loki-compose.yaml",
            "up",
            "-d",
            "loki",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd="/home/j/live/dinesh/llm-chatbot-python/infrastructure/monitoring/component/loki",
        )

        activity.logger.info(f"Docker-compose output: {result.stdout}")
        if result.stderr:
            activity.logger.warning(f"Docker-compose warnings: {result.stderr}")

    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Docker-compose failed: {e.stderr}")
        raise Exception(f"Failed to start Loki via docker-compose: {e}") from e


async def _wait_for_healthy_loki(container) -> bool:
    """Wait for the Loki container to become healthy by checking its ready endpoint.

    This function implements a polling mechanism to wait for Loki to become
    ready. It checks the container status and performs HTTP requests to the
    /ready endpoint until Loki responds successfully.

    Args:
        container: Docker container object to monitor for health.

    Returns:
        bool: True when the Loki health check passes.

    Raises:
        Exception: If the container doesn't become healthy within the timeout period
                  or if the container status becomes non-running.

    Configuration:
        - max_wait_time: Maximum time to wait (300 seconds = 5 minutes)
        - check_interval: Time between health checks (10 seconds)
        - health_endpoint: HTTP endpoint to check (http://localhost:3100/ready)
        - request_timeout: Timeout for individual health check requests (5 seconds)

    """
    import asyncio
    import time
    import urllib.request

    max_wait_time = 300
    check_interval = 10

    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        try:
            container.reload()

            if container.status != "running":
                raise Exception(f"Container is not running. Status: {container.status}")

            try:
                with urllib.request.urlopen(
                    "http://localhost:3100/ready", timeout=5
                ) as response:
                    if response.status == 200:
                        activity.logger.info("Loki is healthy!")
                        return True
            except (urllib.error.URLError, OSError):
                pass

        except Exception as e:
            activity.logger.warning(f"Loki health check failed: {e!s}")

        activity.logger.info(
            f"Waiting for Loki to become healthy... ({time.time() - start_time:.0f}s)"
        )
        await asyncio.sleep(check_interval)

    raise Exception(f"Loki did not become healthy within {max_wait_time} seconds")
