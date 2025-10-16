"""Temporal activities for managing application containers.

This module provides Temporal activities to start and stop Docker containers,
specifically designed for the ai-proxy-service in the LLM chatbot infrastructure.
It handles container lifecycle management, health checking, and integrates with
docker-compose for service orchestration.

The activities in this module are designed to work with the existing
docker-compose.yml configuration and provide robust error handling and logging
for production deployments.

Activities:
    - start_app_container: Starts the ai-proxy-service container and waits for it to become healthy
    - stop_app_container: Stops the ai-proxy-service container gracefully

Dependencies:
    - docker: For container management
    - asyncio: For async health checking
    - subprocess: For docker-compose integration

"""

from temporalio import activity


@activity.defn
async def start_app_container(service_name: str) -> bool:
    """Start the ai-proxy-service container and wait until it is healthy.

    This activity manages the complete lifecycle of starting the ai-proxy-service
    container, including checking if it already exists, starting it if needed,
    and waiting for the health endpoint to respond successfully.

    The activity integrates with the existing docker-compose.yml configuration
    and uses the health check endpoint defined in the service specification.

    Args:
        service_name: Name of the service to start (e.g., "ai-proxy-service").
                     Currently hardcoded to work with "ai-proxy-api" container.

    Returns:
        bool: True if the container started successfully and is healthy.

    Raises:
        Exception: If the container fails to start within the timeout period
                  or if the health check fails.

    Example:
        >>> await start_app_container("ai-proxy-service")
        True

    """
    import urllib.request

    activity.logger.info(f"Starting container for service: {service_name}")

    import docker

    try:
        client = docker.from_env()

        container_name = "ai-proxy-api"
        try:
            container = client.containers.get(container_name)
            if container.status == "running":
                activity.logger.info(f"Container {container_name} is already running")
                # Check if it's healthy first
                try:
                    with urllib.request.urlopen(
                        "http://localhost:8001/health", timeout=5
                    ) as response:
                        if response.status == 200:
                            activity.logger.info("Container is healthy!")
                            return True
                except (urllib.error.URLError, OSError):
                    activity.logger.info(
                        "Container is running but not healthy, starting via docker-compose"
                    )
                    await _start_container_via_compose()
            else:
                activity.logger.info(f"Starting existing container {container_name}")
                container.start()
        except docker.errors.NotFound:
            activity.logger.info(
                f"Container {container_name} not found, " f"starting via docker-compose"
            )
            await _start_container_via_compose()

        container = client.containers.get(container_name)
        return await _wait_for_healthy_container(container)

    except Exception as e:
        activity.logger.error(f"Failed to start container {service_name}: {e!s}")
        raise


async def _start_container_via_compose() -> None:
    """Start the ai-proxy-service using docker-compose.

    This helper function executes docker-compose up to start the ai-proxy service
    in detached mode. It uses the existing ai-proxy-service.docker-compose.yml configuration
    and runs from the ai-proxy-service directory.

    The function captures both stdout and stderr for proper logging and error
    handling in the Temporal activity context.

    Raises:
        Exception: If docker-compose command fails or returns a non-zero exit code.

    Note:
        This function assumes docker-compose is available in the system PATH
        and that the ai-proxy-service.docker-compose.yml file exists in the ai-proxy-service directory.

    """
    import subprocess

    try:
        cmd = [
            "docker-compose",
            "-f",
            "/home/j/live/dinesh/llm-chatbot-python/infrastructure/services/ai-proxy-service/ai-proxy-service.docker-compose.yml",
            "up",
            "-d",
            "api",
        ]

        activity.logger.info(
            f"Running command: {' '.join(cmd)} in cwd: /home/j/live/dinesh/llm-chatbot-python/infrastructure/services/ai-proxy-service"
        )
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd="/home/j/live/dinesh/llm-chatbot-python/infrastructure/services/ai-proxy-service",
        )

        activity.logger.info(f"Docker-compose output: {result.stdout}")
        if result.stderr:
            activity.logger.warning(f"Docker-compose warnings: {result.stderr}")

    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Docker-compose failed: {e.stderr}")
        activity.logger.error(f"Command: {e.cmd}")
        activity.logger.error(f"Return code: {e.returncode}")
        raise Exception(
            f"Failed to start ai-proxy-service via docker-compose: {e}"
        ) from e


async def _wait_for_healthy_container(container) -> bool:
    """Wait for a Docker container to become healthy by checking its health endpoint.

    This function implements a polling mechanism to wait for a container to become
    healthy. It checks the container status and performs HTTP requests to the
    health endpoint until the container responds with a 200 status code.

    Args:
        container: Docker container object to monitor for health.

    Returns:
        bool: True when the container health check passes.

    Raises:
        Exception: If the container doesn't become healthy within the timeout period
                  or if the container status becomes non-running.

    Configuration:
        - max_wait_time: Maximum time to wait (300 seconds = 5 minutes)
        - check_interval: Time between health checks (10 seconds)
        - health_endpoint: HTTP endpoint to check (http://localhost:8001/health)
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
                    "http://localhost:8001/health", timeout=5
                ) as response:
                    if response.status == 200:
                        activity.logger.info("Container is healthy!")
                        return True
            except (urllib.error.URLError, OSError):
                pass

        except Exception as e:
            activity.logger.warning(f"Health check failed: {e!s}")

        activity.logger.info(
            f"Waiting for container to become healthy... ({time.time() - start_time:.0f}s)"
        )
        await asyncio.sleep(check_interval)

    raise Exception(f"Container did not become healthy within {max_wait_time} seconds")


@activity.defn
async def stop_app_container(service_name: str) -> bool:
    """Stop the ai-proxy-service container gracefully.

    This activity stops the ai-proxy-service container using the Docker SDK.
    It waits for the container to fully stop before returning, ensuring
    a clean shutdown process.

    Args:
        service_name: Name of the service to stop. Used for logging purposes.

    Returns:
        bool: True if the container was stopped successfully.

    Raises:
        Exception: If the container cannot be found or fails to stop properly.

    Example:
        >>> await stop_app_container("ai-proxy-service")
        True

    """
    activity.logger.info(f"Stopping container for service: {service_name}")

    import docker

    try:
        client = docker.from_env()
        container_name = "ai-proxy-api"

        container = client.containers.get(container_name)
        container.stop()
        container.wait()

        activity.logger.info(f"Successfully stopped container {container_name}")
        return True

    except Exception as e:
        activity.logger.error(f"Failed to stop container {service_name}: {e!s}")
        raise
