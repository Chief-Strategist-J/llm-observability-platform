"""Temporal activity for managing Grafana container.

This module provides a Temporal activity to start the Grafana monitoring container,
which provides visualization and dashboards for the monitoring infrastructure. It
handles container lifecycle management and health checking to ensure Grafana is ready to
serve dashboards.

"""

from temporalio import activity


@activity.defn
async def start_grafana(environment: str = "production") -> bool:
    """Start the Grafana monitoring container and wait until it is healthy.

    This activity manages the complete lifecycle of starting the Grafana container,
    including checking if it already exists, starting it if needed, and waiting
    for the health endpoint to respond successfully.

    The activity uses the existing docker-compose configuration for the Grafana service,
    which runs on different ports based on the environment (development, staging, production).

    Args:
        environment: The Grafana environment to start ("development", "staging", or "production").
                     Defaults to "production".

    Returns:
        bool: True if the Grafana container started successfully and is healthy.

    Raises:
        Exception: If the container fails to start within the timeout period
                  or if the health check fails.

    Example:
        >>> await start_grafana("production")
        True

    """
    activity.logger.info(f"Starting Grafana container for environment: {environment}")

    import docker

    try:
        client = docker.from_env()

        container_name = f"grafana-{environment}"
        port = {"development": 31001, "staging": 31002, "production": 31003}[
            environment
        ]

        try:
            container = client.containers.get(container_name)
            if container.status == "running":
                activity.logger.info(f"Container {container_name} is already running")
                return await _wait_for_healthy_grafana(container, port)
            activity.logger.info(f"Starting existing container {container_name}")
            container.start()
        except docker.errors.NotFound:
            activity.logger.info(
                f"Container {container_name} not found, " f"starting via docker-compose"
            )
            await _start_grafana_via_compose(environment)

        container = client.containers.get(container_name)
        return await _wait_for_healthy_grafana(container, port)

    except Exception as e:
        activity.logger.error(
            f"Failed to start Grafana container for {environment}: {e!s}"
        )
        raise


async def _start_grafana_via_compose(environment: str) -> None:
    """Start the Grafana service using docker-compose.

    This helper function executes docker-compose up to start the Grafana service
    in detached mode for the specified environment. It uses the existing
    dashboard-grafana-compose.yaml configuration and runs from the Grafana component directory.

    Args:
        environment: The Grafana environment to start ("development", "staging", or "production").

    Raises:
        Exception: If docker-compose command fails or returns a non-zero exit code.

    Note:
        This function assumes docker-compose is available in the system PATH
        and that the dashboard-grafana-compose.yaml file exists in the Grafana component directory.

    """
    import subprocess

    try:
        cmd = [
            "docker-compose",
            "-f",
            "/home/j/live/dinesh/llm-chatbot-python/infrastructure/monitoring/component/grafana/dashboard-grafana-compose.yaml",
            "up",
            "-d",
            f"grafana-{environment}",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd="/home/j/live/dinesh/llm-chatbot-python/infrastructure/monitoring/component/grafana",
        )

        activity.logger.info(f"Docker-compose output: {result.stdout}")
        if result.stderr:
            activity.logger.warning(f"Docker-compose warnings: {result.stderr}")

    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Docker-compose failed: {e.stderr}")
        raise Exception(f"Failed to start Grafana via docker-compose: {e}") from e


async def _wait_for_healthy_grafana(container, port: int) -> bool:
    """Wait for the Grafana container to become healthy by checking its health endpoint.

    This function implements a polling mechanism to wait for Grafana to become
    healthy. It checks the container status and performs HTTP requests to the
    /api/health endpoint until Grafana responds successfully.

    Args:
        container: Docker container object to monitor for health.
        port: The port number where Grafana is accessible.

    Returns:
        bool: True when the Grafana health check passes.

    Raises:
        Exception: If the container doesn't become healthy within the timeout period
                  or if the container status becomes non-running.

    Configuration:
        - max_wait_time: Maximum time to wait (300 seconds = 5 minutes)
        - check_interval: Time between health checks (10 seconds)
        - health_endpoint: HTTP endpoint to check (http://localhost:{port}/api/health)
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
                    f"http://localhost:{port}/api/health", timeout=5
                ) as response:
                    if response.status == 200:
                        activity.logger.info("Grafana is healthy!")
                        return True
            except (urllib.error.URLError, OSError):
                pass

        except Exception as e:
            activity.logger.warning(f"Grafana health check failed: {e!s}")

        activity.logger.info(
            f"Waiting for Grafana to become healthy... ({time.time() - start_time:.0f}s)"
        )
        await asyncio.sleep(check_interval)

    raise Exception(f"Grafana did not become healthy within {max_wait_time} seconds")
