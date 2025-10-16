"""Temporal activities for managing application containers.

This module provides Temporal activities to start and stop Docker containers,
specifically designed for the ai-proxy-service in the LLM chatbot infrastructure.
It handles container lifecycle management, health checking, and integrates with
docker-compose for service orchestration.

The activities in this module are designed to work with the existing
docker-compose.yml configuration and provide robust error handling and logging
for production deployments.

Activities:
    - start_app_container: Starts the ai-proxy-service container and waits for
      it to become healthy
    - stop_app_container: Stops the ai-proxy-service container gracefully

Dependencies:
    - docker: For container management
    - asyncio: For async health checking
    - subprocess: For docker-compose integration

"""

import asyncio
import subprocess
import time
import urllib.request

import docker
from temporalio import activity


class ContainerConfig:
    """
    Configuration for container management activities.
    """

    CONTAINER_NAME = "ai-proxy-api"
    SERVICE_NAME = "api"

    PROJECT_ROOT = "/home/j/live/dinesh/llm-chatbot-python"
    SERVICE_DIR = f"{PROJECT_ROOT}/infrastructure/services/ai-proxy-service"
    COMPOSE_FILE = f"{SERVICE_DIR}/ai-proxy-service.docker-compose.yml"

    HEALTH_ENDPOINT = "http://localhost:8001/health"
    HEALTH_CHECK_TIMEOUT = 5
    HEALTH_CHECK_INTERVAL = 10
    MAX_WAIT_TIME = 300

    HTTP_OK = 200


@activity.defn
async def start_app_container(service_name: str) -> bool:
    """Start the ai-proxy-service container and wait until it is healthy.

    This activity manages the complete lifecycle of starting the
    ai-proxy-service container, including checking if it already exists,
    starting it if needed, and waiting for the health endpoint to respond
    successfully.

    The activity integrates with the existing docker-compose.yml
    configuration and uses the health check endpoint defined in the service
    specification.

    Args:
        service_name: Name of the service to start (e.g.,
                     "ai-proxy-service"). Currently hardcoded to work with
                     "ai-proxy-api" container.

    Returns:
        bool: True if the container started successfully and is healthy.

    Raises:
        RuntimeError: If the container fails to start within the timeout
                     period or if the health check fails.

    Example:
        >>> await start_app_container("ai-proxy-service")
        True

    """
    activity.logger.info(f"Starting container for service: {service_name}")

    try:
        client = docker.from_env()
        container = await _get_or_start_container(client)
        return await _wait_for_healthy_container(container)

    except Exception as e:
        error_msg = f"Failed to start container {service_name}: {e!s}"
        activity.logger.error(error_msg)
        raise RuntimeError(error_msg) from e


@activity.defn
async def stop_app_container(service_name: str) -> bool:
    """Stop the ai-proxy-service container gracefully.

    This activity stops the ai-proxy-service container using the Docker SDK.
    It waits for the container to fully stop before returning, ensuring
    a clean shutdown process.

    Args:
        service_name: Name of the service to stop. Used for logging
                     purposes.

    Returns:
        bool: True if the container was stopped successfully.

    Raises:
        RuntimeError: If the container cannot be found or fails to stop
                     properly.

    Example:
        >>> await stop_app_container("ai-proxy-service")
        True

    """
    activity.logger.info(f"Stopping container for service: {service_name}")

    try:
        client = docker.from_env()
        container = client.containers.get(ContainerConfig.CONTAINER_NAME)
        container.stop()
        container.wait()

        activity.logger.info(
            f"Successfully stopped container {ContainerConfig.CONTAINER_NAME}"
        )
        return True

    except Exception as e:
        error_msg = f"Failed to stop container {service_name}: {e!s}"
        activity.logger.error(error_msg)
        raise RuntimeError(error_msg) from e


async def _get_or_start_container(client):
    """Get existing container or start a new one.

    Args:
        client: Docker client instance.

    Returns:
        Docker container object.

    """
    try:
        container = client.containers.get(ContainerConfig.CONTAINER_NAME)

        if container.status == "running":
            log_msg = (
                f"Container {ContainerConfig.CONTAINER_NAME} is already " "running"
            )
            activity.logger.info(log_msg)

            if await _check_container_health():
                activity.logger.info("Container is healthy!")
                return container

            log_msg = (
                "Container is running but not healthy, restarting via " "docker-compose"
            )
            activity.logger.info(log_msg)
            await _start_container_via_compose()
        else:
            log_msg = (
                f"Starting existing container " f"{ContainerConfig.CONTAINER_NAME}"
            )
            activity.logger.info(log_msg)
            container.start()

    except docker.errors.NotFound:
        log_msg = (
            f"Container {ContainerConfig.CONTAINER_NAME} not found, "
            "starting via docker-compose"
        )
        activity.logger.info(log_msg)
        await _start_container_via_compose()

    return client.containers.get(ContainerConfig.CONTAINER_NAME)


async def _check_container_health() -> bool:
    """Check if the container health endpoint is responding.

    Returns:
        bool: True if health check passes, False otherwise.

    """
    try:
        with urllib.request.urlopen(
            ContainerConfig.HEALTH_ENDPOINT,
            timeout=ContainerConfig.HEALTH_CHECK_TIMEOUT,
        ) as response:
            return response.status == ContainerConfig.HTTP_OK
    except (urllib.error.URLError, OSError):
        return False


async def _start_container_via_compose() -> None:
    """Start the ai-proxy-service using docker-compose.

    This helper function executes docker-compose up to start the ai-proxy
    service in detached mode. It uses the existing
    ai-proxy-service.docker-compose.yml configuration and runs from the
    ai-proxy-service directory.

    The function captures both stdout and stderr for proper logging and
    error handling in the Temporal activity context.

    Raises:
        RuntimeError: If docker-compose command fails or returns a non-zero
                     exit code.

    Note:
        This function assumes docker-compose is available in the system PATH
        and that the ai-proxy-service.docker-compose.yml file exists in the
        ai-proxy-service directory.

    """
    try:
        cmd = [
            "docker-compose",
            "-f",
            ContainerConfig.COMPOSE_FILE,
            "up",
            "-d",
            ContainerConfig.SERVICE_NAME,
        ]

        log_msg = (
            f"Running command: {' '.join(cmd)} "
            f"in cwd: {ContainerConfig.SERVICE_DIR}"
        )
        activity.logger.info(log_msg)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=ContainerConfig.SERVICE_DIR,
        )

        activity.logger.info(f"Docker-compose output: {result.stdout}")
        if result.stderr:
            activity.logger.warning(f"Docker-compose warnings: {result.stderr}")

    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Docker-compose failed: {e.stderr}")
        activity.logger.error(f"Command: {e.cmd}")
        activity.logger.error(f"Return code: {e.returncode}")
        error_msg = f"Failed to start ai-proxy-service via docker-compose: {e}"
        raise RuntimeError(error_msg) from e


async def _wait_for_healthy_container(container) -> bool:
    """Wait for a Docker container to become healthy by checking endpoint.

    This function implements a polling mechanism to wait for a container to
    become healthy. It checks the container status and performs HTTP
    requests to the health endpoint until the container responds with a 200
    status code.

    Args:
        container: Docker container object to monitor for health.

    Returns:
        bool: True when the container health check passes.

    Raises:
        RuntimeError: If the container doesn't become healthy within the
                     timeout period or if the container status becomes
                     non-running.

    """
    start_time = time.time()

    while time.time() - start_time < ContainerConfig.MAX_WAIT_TIME:
        try:
            container.reload()

            if container.status != "running":
                error_msg = f"Container is not running. Status: " f"{container.status}"
                raise RuntimeError(error_msg)

            if await _check_container_health():
                activity.logger.info("Container is healthy!")
                return True

        except Exception as e:
            activity.logger.warning(f"Health check failed: {e!s}")

        elapsed_time = time.time() - start_time
        log_msg = (
            f"Waiting for container to become healthy... " f"({elapsed_time:.0f}s)"
        )
        activity.logger.info(log_msg)
        await asyncio.sleep(ContainerConfig.HEALTH_CHECK_INTERVAL)

    error_msg = (
        f"Container did not become healthy within "
        f"{ContainerConfig.MAX_WAIT_TIME} seconds"
    )
    raise RuntimeError(error_msg)
