"""Temporal activity for managing Promtail container.

This module provides a Temporal activity to start the Promtail log shipping container,
which forwards logs to Loki as part of the monitoring infrastructure. It handles
container lifecycle management and ensures Promtail is running and ready.

"""

from temporalio import activity


@activity.defn
async def start_promtail() -> bool:
    """Start the Promtail log shipping container.

    This activity manages the lifecycle of starting the Promtail container,
    which is responsible for collecting logs from the host and shipping them to Loki.
    Since Promtail doesn't have a specific health endpoint, we verify it's running
    and wait for it to initialize.

    The activity uses the existing docker-compose configuration for the Promtail service,
    which runs as a log collection agent.

    Returns:
        bool: True if the Promtail container started successfully and is running.

    Raises:
        Exception: If the container fails to start or isn't running after the timeout.

    Example:
        >>> await start_promtail()
        True

    """
    activity.logger.info("Starting Promtail container")

    import docker

    try:
        client = docker.from_env()

        container_name = "promtail"
        try:
            container = client.containers.get(container_name)
            if container.status == "running":
                activity.logger.info(f"Container {container_name} is already running")
                return True
            activity.logger.info(f"Starting existing container {container_name}")
            container.start()
        except docker.errors.NotFound:
            activity.logger.info(
                f"Container {container_name} not found, " f"starting via docker-compose"
            )
            await _start_promtail_via_compose()

        container = client.containers.get(container_name)
        return await _wait_for_running_promtail(container)

    except Exception as e:
        activity.logger.error(f"Failed to start Promtail container: {e!s}")
        raise


async def _start_promtail_via_compose() -> None:
    """Start the Promtail service using docker-compose.

    This helper function executes docker-compose up to start the Promtail service
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
            "promtail",
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
        raise Exception(f"Failed to start Promtail via docker-compose: {e}") from e


async def _wait_for_running_promtail(container) -> bool:
    """Wait for the Promtail container to be running and initialized.

    Since Promtail doesn't have a health endpoint, we simply wait for the container
    to be in a running state and allow time for it to initialize. Promtail is designed
    to be resilient and will automatically attempt to reconnect to Loki if needed.

    Args:
        container: Docker container object to monitor.

    Returns:
        bool: True when the Promtail container is running.

    Raises:
        Exception: If the container isn't running after the timeout period.

    Configuration:
        - max_wait_time: Maximum time to wait (60 seconds)
        - check_interval: Time between status checks (5 seconds)

    """
    import asyncio
    import time

    max_wait_time = 60
    check_interval = 5

    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        try:
            container.reload()

            if container.status == "running":
                activity.logger.info("Promtail is running!")
                return True

        except Exception as e:
            activity.logger.warning(f"Promtail status check failed: {e!s}")

        activity.logger.info(
            f"Waiting for Promtail to start... ({time.time() - start_time:.0f}s)"
        )
        await asyncio.sleep(check_interval)

    raise Exception(f"Promtail did not start within {max_wait_time} seconds")
