"""Temporal activity for managing Grafana container.

This module provides a Temporal activity to start the Grafana monitoring container,
which provides visualization and dashboards for the monitoring infrastructure. It
handles container lifecycle management and health checking to ensure Grafana is ready to
serve dashboards.

"""

import asyncio
import subprocess
import time
import urllib.request

import docker
from temporalio import activity


class GrafanaConfig:
    """
    Configuration for Grafana container management.
    """

    PORTS = {"development": 31001, "staging": 31002, "production": 31003}

    PROJECT_ROOT = "/home/j/live/dinesh/llm-chatbot-python"
    GRAFANA_DIR = f"{PROJECT_ROOT}/infrastructure/monitoring/component/grafana"
    COMPOSE_FILE = f"{GRAFANA_DIR}/dashboard-grafana-compose.yaml"

    HEALTH_ENDPOINT_TEMPLATE = "http://localhost:{port}/api/health"
    REQUEST_TIMEOUT = 5
    CHECK_INTERVAL = 10
    MAX_WAIT_TIME = 300

    HTTP_OK = 200


@activity.defn
async def start_grafana(environment: str = "production") -> bool:
    """Start the Grafana monitoring container and wait until it is healthy.

    This activity manages the complete lifecycle of starting the Grafana
    container, including checking if it already exists, starting it if
    needed, and waiting for the health endpoint to respond successfully.

    The activity uses the existing docker-compose configuration for the
    Grafana service, which runs on different ports based on the environment
    (development, staging, production).

    Args:
        environment: The Grafana environment to start ("development",
                    "staging", or "production"). Defaults to "production".

    Returns:
        bool: True if the Grafana container started successfully and is
             healthy.

    Raises:
        RuntimeError: If the container fails to start within the timeout
                     period or if the health check fails.

    Example:
        >>> await start_grafana("production")
        True

    """
    activity.logger.info(f"Starting Grafana container for environment: {environment}")

    try:
        client = docker.from_env()
        container_name = f"grafana-{environment}"
        port = GrafanaConfig.PORTS[environment]

        container = await _get_or_start_grafana(
            client, container_name, environment, port
        )
        return await _wait_for_healthy_grafana(container, port)

    except Exception as e:
        error_msg = f"Failed to start Grafana container for {environment}: {e!s}"
        activity.logger.error(error_msg)
        raise RuntimeError(error_msg) from e


async def _get_or_start_grafana(client, container_name, environment, port):
    """Get existing Grafana container or start a new one.

    Args:
        client: Docker client instance.
        container_name: Name of the Grafana container.
        environment: Environment name.
        port: Port number for health checks.

    Returns:
        Docker container object.

    """
    try:
        container = client.containers.get(container_name)

        if container.status == "running":
            activity.logger.info(f"Container {container_name} is already running")
            return container

        activity.logger.info(f"Starting existing container {container_name}")
        container.start()

    except docker.errors.NotFound:
        log_msg = (
            f"Container {container_name} not found, starting via " "docker-compose"
        )
        activity.logger.info(log_msg)
        await _start_grafana_via_compose(environment)

    return client.containers.get(container_name)


async def _start_grafana_via_compose(environment: str) -> None:
    """Start the Grafana service using docker-compose.

    This helper function executes docker-compose up to start the Grafana
    service in detached mode for the specified environment. It uses the
    existing dashboard-grafana-compose.yaml configuration and runs from the
    Grafana component directory.

    Args:
        environment: The Grafana environment to start ("development",
                    "staging", or "production").

    Raises:
        RuntimeError: If docker-compose command fails or returns a non-zero
                     exit code.

    Note:
        This function assumes docker-compose is available in the system PATH
        and that the dashboard-grafana-compose.yaml file exists in the
        Grafana component directory.

    """
    try:
        cmd = [
            "docker-compose",
            "-f",
            GrafanaConfig.COMPOSE_FILE,
            "up",
            "-d",
            f"grafana-{environment}",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=GrafanaConfig.GRAFANA_DIR,
        )

        activity.logger.info(f"Docker-compose output: {result.stdout}")
        if result.stderr:
            activity.logger.warning(f"Docker-compose warnings: {result.stderr}")

    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Docker-compose failed: {e.stderr}")
        error_msg = f"Failed to start Grafana via docker-compose: {e}"
        raise RuntimeError(error_msg) from e


async def _wait_for_healthy_grafana(container, port: int) -> bool:
    """Wait for the Grafana container to become healthy.

    This function implements a polling mechanism to wait for Grafana to
    become healthy. It checks the container status and performs HTTP
    requests to the /api/health endpoint until Grafana responds
    successfully.

    Args:
        container: Docker container object to monitor for health.
        port: The port number where Grafana is accessible.

    Returns:
        bool: True when the Grafana health check passes.

    Raises:
        RuntimeError: If the container doesn't become healthy within the
                     timeout period or if the container status becomes
                     non-running.

    """
    start_time = time.time()

    while time.time() - start_time < GrafanaConfig.MAX_WAIT_TIME:
        try:
            container.reload()

            if container.status != "running":
                error_msg = f"Container is not running. Status: " f"{container.status}"
                raise RuntimeError(error_msg)

            health_endpoint = GrafanaConfig.HEALTH_ENDPOINT_TEMPLATE.format(port=port)
            try:
                with urllib.request.urlopen(
                    health_endpoint, timeout=GrafanaConfig.REQUEST_TIMEOUT
                ) as response:
                    if response.status == GrafanaConfig.HTTP_OK:
                        activity.logger.info("Grafana is healthy!")
                        return True
            except (urllib.error.URLError, OSError):
                pass

        except Exception as e:
            activity.logger.warning(f"Grafana health check failed: {e!s}")

        elapsed_time = time.time() - start_time
        log_msg = f"Waiting for Grafana to become healthy... " f"({elapsed_time:.0f}s)"
        activity.logger.info(log_msg)
        await asyncio.sleep(GrafanaConfig.CHECK_INTERVAL)

    error_msg = (
        f"Grafana did not become healthy within "
        f"{GrafanaConfig.MAX_WAIT_TIME} seconds"
    )
    raise RuntimeError(error_msg)
