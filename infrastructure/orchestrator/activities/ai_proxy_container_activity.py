"""Temporal activities for managing application containers.

This module provides Temporal activities to start and stop Docker containers,
specifically designed for the ai-proxy-service in the LLM chatbot infrastructure.
It handles container lifecycle management, health checking and integrates with
docker-compose for service orchestration.

The activities in this module are designed to work with the existing
docker-compose.yml configuration and provide robust error handling and logging
for production deployments.

Activities:
    - start_app_container: Starts the ai-proxy-service container and waits for
      it to become healthy
    - stop_app_container: Stops the ai-proxy-service container gracefully and
      cleans up resources

Dependencies:
    - docker: For container management
    - asyncio: For async health checking
    - subprocess: For docker-compose integration

"""

import asyncio
import os
from pathlib import Path
import subprocess
import time

import docker
from temporalio import activity


class ContainerConfig:
    """
    Configuration for container management activities.
    """

    CONTAINER_NAME = "ai-proxy-api"
    SERVICE_NAME = "api"
    _current_file = Path(__file__)
    PROJECT_ROOT = str(_current_file.parent.parent.parent.parent.resolve())
    SERVICE_DIR = os.path.join(
        PROJECT_ROOT, "infrastructure", "services", "ai-proxy-service"
    )
    COMPOSE_FILE = os.path.join(SERVICE_DIR, "ai-proxy-service.docker-compose.yml")

    HEALTH_ENDPOINT = "http://localhost:8001/health"
    HEALTH_CHECK_TIMEOUT = 5
    HEALTH_CHECK_INTERVAL = 10
    MAX_WAIT_TIME = 300
    MAX_RACE_RETRIES = 3

    HTTP_OK = 200


@activity.defn
async def start_app_container(service_name: str) -> bool:
    """
    Start the ai-proxy-service container and wait until it is healthy.
    """
    activity.logger.info(f"Starting container for service: {service_name}")

    try:
        # Build the container first
        await _build_container_via_compose()

        client = docker.from_env()
        race_attempts = 0

        while race_attempts < ContainerConfig.MAX_RACE_RETRIES:
            try:
                container = await _get_or_start_container(client)
                return await _wait_for_healthy_container(container)
            except RuntimeError as e:
                race_attempts += 1
                activity.logger.warning(
                    f"Attempt {race_attempts} failed due to potential race condition: {e}"
                )
                await asyncio.sleep(2)

        # If all attempts fail, fetch logs and fail
        await _fetch_container_logs()
        raise RuntimeError("Container failed to become healthy after multiple attempts")

    except Exception as e:
        activity.logger.error(f"Failed to start container: {e}")
        await _fetch_container_logs()
        raise


@activity.defn
async def stop_app_container(service_name: str) -> bool:
    """
    Stop the ai-proxy-service container and clean up all resources.
    """
    activity.logger.info(f"Stopping and cleaning container for service: {service_name}")

    client = docker.from_env()

    # Auto-discover container by service name pattern
    containers_to_stop = []
    for container in client.containers.list(all=True):
        if (
            service_name in container.name
            or ContainerConfig.CONTAINER_NAME in container.name
        ):
            containers_to_stop.append(container)
            activity.logger.info(
                f"Found container to stop: {container.name} (ID: {container.id[:12]})"
            )

    if not containers_to_stop:
        activity.logger.info(f"No containers found for service: {service_name}")
        return True

    # Stop and clean all found containers
    for container in containers_to_stop:
        await _stop_and_clean_container(client, container)

    # Clean up orphaned volumes and networks
    await _cleanup_orphaned_resources(client, service_name)

    return True


async def _stop_and_clean_container(client, container):
    """
    Stop and completely clean a single container and all its resources.
    """
    container_name = container.name

    try:
        # Stop container with timeout
        activity.logger.info(f"Stopping container {container_name}...")
        container.stop(timeout=30)
        container.wait()
        activity.logger.info(f"Container {container_name} stopped successfully")

        # Remove container
        activity.logger.info(f"Removing container {container_name}...")
        container.remove(force=True)
        activity.logger.info(f"Container {container_name} removed successfully")

        # Remove associated volumes
        await _remove_container_volumes(client, container)

        # Remove associated networks (if not default)
        await _remove_container_networks(client, container)

    except Exception as e:
        activity.logger.error(f"Failed to stop container {container_name}: {e}")
        # Try force removal even if stop failed
        try:
            container.remove(force=True)
            activity.logger.info(f"Force removed container {container_name}")
        except Exception as e2:
            activity.logger.error(
                f"Failed to force remove container {container_name}: {e2}"
            )


async def _remove_container_volumes(client, container):
    """
    Remove volumes associated with a container.
    """
    try:
        # Get volumes from container mounts
        for mount in container.attrs.get("Mounts", []):
            if mount.get("Name"):
                volume_name = mount["Name"]
                try:
                    volume = client.volumes.get(volume_name)
                    volume.remove(force=True)
                    activity.logger.info(f"Removed volume: {volume_name}")
                except docker.errors.NotFound:
                    activity.logger.debug(
                        f"Volume {volume_name} not found, skipping removal"
                    )
                except Exception as e:
                    activity.logger.error(f"Failed to remove volume {volume_name}: {e}")

        # Also check for volumes with service name pattern
        for volume in client.volumes.list():
            if service_name in volume.name:
                try:
                    volume.remove(force=True)
                    activity.logger.info(f"Removed orphaned volume: {volume.name}")
                except Exception as e:
                    activity.logger.error(f"Failed to remove volume {volume.name}: {e}")

    except Exception as e:
        activity.logger.error(f"Error during volume cleanup: {e}")


async def _remove_container_networks(client, container):
    """
    Remove networks associated with a container (except default networks).
    """
    try:
        for net_name, net_info in (
            container.attrs.get("NetworkSettings", {}).get("Networks", {}).items()
        ):
            if net_name not in ["bridge", "host", "none"]:
                try:
                    network = client.networks.get(net_name)
                    network.remove()
                    activity.logger.info(f"Removed network: {net_name}")
                except docker.errors.NotFound:
                    activity.logger.debug(
                        f"Network {net_name} not found, skipping removal"
                    )
                except Exception as e:
                    activity.logger.error(f"Failed to remove network {net_name}: {e}")

    except Exception as e:
        activity.logger.error(f"Error during network cleanup: {e}")


async def _cleanup_orphaned_resources(client, service_name):
    """
    Clean up any orphaned resources related to the service.
    """
    try:
        # Remove images with service name pattern
        for image in client.images.list():
            for tag in image.tags:
                if service_name in tag:
                    try:
                        client.images.remove(image.id, force=True)
                        activity.logger.info(f"Removed orphaned image: {tag}")
                    except Exception as e:
                        activity.logger.error(f"Failed to remove image {tag}: {e}")

        # Remove any remaining networks with service pattern
        for network in client.networks.list():
            if service_name in network.name:
                try:
                    network.remove()
                    activity.logger.info(f"Removed orphaned network: {network.name}")
                except Exception as e:
                    activity.logger.error(
                        f"Failed to remove network {network.name}: {e}"
                    )

    except Exception as e:
        activity.logger.error(f"Error during orphaned resource cleanup: {e}")


async def _build_container_via_compose() -> None:
    """
    Build the container using docker-compose.
    """
    cmd = [
        "docker-compose",
        "-f",
        ContainerConfig.COMPOSE_FILE,
        "build",
        ContainerConfig.SERVICE_NAME,
    ]
    try:
        activity.logger.info(f"Building container: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=ContainerConfig.SERVICE_DIR,
        )
        activity.logger.info(f"Docker-compose build output: {result.stdout}")
        if result.stderr:
            activity.logger.warning(f"Docker-compose build warnings: {result.stderr}")
    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Docker-compose build failed: {e.stderr}")
        raise RuntimeError(f"Failed to build container: {e}") from e


async def _get_or_start_container(client):
    """
    Get existing container or start a new one.
    """
    try:
        container = client.containers.get(ContainerConfig.CONTAINER_NAME)
        container.reload()

        if container.status == "running":
            activity.logger.info(
                f"Container {ContainerConfig.CONTAINER_NAME} is already running"
            )
            if await _check_container_health():
                activity.logger.info("Container is healthy!")
                return container
            activity.logger.info("Container not healthy, restarting via docker-compose")
            await _start_container_via_compose()
        else:
            activity.logger.info(
                f"Starting existing container {ContainerConfig.CONTAINER_NAME}"
            )
            container.start()
    except docker.errors.NotFound:
        activity.logger.info(
            f"Container {ContainerConfig.CONTAINER_NAME} not found, starting via docker-compose"
        )
        await _start_container_via_compose()

    return client.containers.get(ContainerConfig.CONTAINER_NAME)


async def _check_container_health() -> bool:
    """
    Check if the container health endpoint is responding.
    """
    import urllib.request

    try:
        with urllib.request.urlopen(
            ContainerConfig.HEALTH_ENDPOINT,
            timeout=ContainerConfig.HEALTH_CHECK_TIMEOUT,
        ) as response:
            return response.status == ContainerConfig.HTTP_OK
    except (urllib.error.URLError, OSError):
        return False


async def _start_container_via_compose() -> None:
    """
    Start the ai-proxy-service using docker-compose.
    """
    cmd = [
        "docker-compose",
        "-f",
        ContainerConfig.COMPOSE_FILE,
        "up",
        "-d",
        ContainerConfig.SERVICE_NAME,
    ]
    try:
        activity.logger.info(f"Starting container via docker-compose: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=ContainerConfig.SERVICE_DIR,
        )
        activity.logger.info(f"Docker-compose up output: {result.stdout}")
        if result.stderr:
            activity.logger.warning(f"Docker-compose up warnings: {result.stderr}")
    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Docker-compose up failed: {e.stderr}")
        raise RuntimeError(f"Failed to start container via docker-compose: {e}") from e


async def _wait_for_healthy_container(container) -> bool:
    """
    Wait for a Docker container to become healthy by checking HTTP endpoint.
    """
    import urllib.request

    start_time = time.time()
    while time.time() - start_time < ContainerConfig.MAX_WAIT_TIME:
        try:
            container.reload()
            if container.status != "running":
                raise RuntimeError(
                    f"Container stopped unexpectedly (status={container.status})"
                )
            with urllib.request.urlopen(
                ContainerConfig.HEALTH_ENDPOINT,
                timeout=ContainerConfig.HEALTH_CHECK_TIMEOUT,
            ) as response:
                if response.status == ContainerConfig.HTTP_OK:
                    activity.logger.info("Container HTTP health check passed!")
                    return True
        except Exception as e:
            activity.logger.debug(f"Health check failed: {e}")
            # Immediate retry - no artificial delays

    raise RuntimeError(
        f"Container did not become healthy within {ContainerConfig.MAX_WAIT_TIME} seconds"
    )


async def _fetch_container_logs():
    """
    Fetch and report Docker logs for the container.
    """
    try:
        client = docker.from_env()
        container = client.containers.get(ContainerConfig.CONTAINER_NAME)
        logs = container.logs(tail=1000).decode("utf-8", errors="replace")
        activity.logger.error(
            f"Docker logs for {ContainerConfig.CONTAINER_NAME}:\n{logs}"
        )
    except docker.errors.NotFound:
        activity.logger.error(
            f"Cannot fetch logs: container {ContainerConfig.CONTAINER_NAME} not found"
        )
    except Exception as e:
        activity.logger.error(f"Failed to fetch Docker logs: {e}")
