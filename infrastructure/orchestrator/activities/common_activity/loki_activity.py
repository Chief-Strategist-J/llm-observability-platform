"""Temporal activities for managing Loki log aggregation containers.

This module provides Temporal activities to start and stop Loki containers
in the monitoring infrastructure.

Activities:
    - start_loki_container: Starts the Loki container and waits for health
    - stop_loki_container: Stops the Loki container and cleans up resources
"""

import asyncio
import os
from pathlib import Path
import subprocess
import time

import docker
from temporalio import activity


class LokiConfig:
    """Configuration for Loki container management."""
    
    CONTAINER_NAME = "loki"
    SERVICE_NAME = "loki"
    _current_file = Path(__file__)
    PROJECT_ROOT = str(_current_file.parent.parent.parent.parent.parent.resolve())
    SERVICE_DIR = os.path.join(
        PROJECT_ROOT, "infrastructure", "monitoring", "component", "loki"
    )
    COMPOSE_FILE = os.path.join(SERVICE_DIR, "logger-loki-compose.yaml")
    
    HEALTH_ENDPOINT = "http://localhost:3100/ready"
    HEALTH_CHECK_TIMEOUT = 5
    HEALTH_CHECK_INTERVAL = 10
    MAX_WAIT_TIME = 120
    MAX_RACE_RETRIES = 3
    
    HTTP_OK = 200


@activity.defn
async def start_loki_container(service_name: str) -> bool:
    """Start the Loki container and wait until it is healthy."""
    activity.logger.info(f"Starting Loki container for service: {service_name}")
    
    try:
        await _build_loki_container()
        client = docker.from_env()
        race_attempts = 0
        
        while race_attempts < LokiConfig.MAX_RACE_RETRIES:
            try:
                container = await _get_or_start_loki_container(client)
                return await _wait_for_healthy_loki(container)
            except RuntimeError as e:
                race_attempts += 1
                activity.logger.warning(f"Attempt {race_attempts} failed: {e}")
                await asyncio.sleep(2)
        
        await _fetch_loki_logs()
        raise RuntimeError("Loki failed to become healthy")
    
    except Exception as e:
        activity.logger.error(f"Failed to start Loki: {e}")
        await _fetch_loki_logs()
        raise


@activity.defn
async def stop_loki_container(service_name: str) -> bool:
    """Stop the Loki container and clean up resources."""
    activity.logger.info(f"Stopping Loki for service: {service_name}")
    
    client = docker.from_env()
    containers_to_stop = []
    
    for container in client.containers.list(all=True):
        if service_name in container.name or LokiConfig.CONTAINER_NAME in container.name:
            containers_to_stop.append(container)
            activity.logger.info(f"Found container: {container.name}")
    
    if not containers_to_stop:
        activity.logger.info(f"No containers found for: {service_name}")
        return True
    
    for container in containers_to_stop:
        await _stop_and_clean_loki_container(client, container)
    
    await _cleanup_loki_resources(client, service_name)
    return True


async def _build_loki_container() -> None:
    """Build the Loki container using docker-compose."""
    cmd = [
        "docker-compose",
        "-f", LokiConfig.COMPOSE_FILE,
        "build", LokiConfig.SERVICE_NAME,
    ]
    try:
        activity.logger.info(f"Building Loki: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            cwd=LokiConfig.SERVICE_DIR,
        )
        activity.logger.info(f"Build output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Build failed: {e.stderr}")
        raise RuntimeError(f"Failed to build Loki: {e}") from e


async def _get_or_start_loki_container(client):
    """Get existing Loki container or start a new one."""
    try:
        container = client.containers.get(LokiConfig.CONTAINER_NAME)
        container.reload()
        
        if container.status == "running":
            activity.logger.info(f"Container {LokiConfig.CONTAINER_NAME} is running")
            if await _check_loki_health():
                activity.logger.info("Loki is healthy!")
                return container
            activity.logger.info("Not healthy, restarting")
            await _start_loki_via_compose()
        else:
            activity.logger.info(f"Starting existing container {LokiConfig.CONTAINER_NAME}")
            container.start()
    except docker.errors.NotFound:
        activity.logger.info(f"Container not found, starting via docker-compose")
        await _start_loki_via_compose()
    
    return client.containers.get(LokiConfig.CONTAINER_NAME)


async def _check_loki_health() -> bool:
    """Check if Loki health endpoint is responding."""
    import urllib.request
    
    try:
        with urllib.request.urlopen(
            LokiConfig.HEALTH_ENDPOINT,
            timeout=LokiConfig.HEALTH_CHECK_TIMEOUT,
        ) as response:
            return response.status == LokiConfig.HTTP_OK
    except (urllib.error.URLError, OSError):
        return False


async def _start_loki_via_compose() -> None:
    """Start Loki using docker-compose."""
    cmd = [
        "docker-compose",
        "-f", LokiConfig.COMPOSE_FILE,
        "up", "-d", LokiConfig.SERVICE_NAME,
    ]
    try:
        activity.logger.info(f"Starting via docker-compose: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            cwd=LokiConfig.SERVICE_DIR,
        )
        activity.logger.info(f"Start output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Start failed: {e.stderr}")
        raise RuntimeError(f"Failed to start Loki: {e}") from e


async def _wait_for_healthy_loki(container) -> bool:
    """Wait for Loki to become healthy."""
    import urllib.request
    
    start_time = time.time()
    while time.time() - start_time < LokiConfig.MAX_WAIT_TIME:
        try:
            container.reload()
            if container.status != "running":
                raise RuntimeError(f"Container stopped (status={container.status})")
            
            with urllib.request.urlopen(
                LokiConfig.HEALTH_ENDPOINT,
                timeout=LokiConfig.HEALTH_CHECK_TIMEOUT,
            ) as response:
                if response.status == LokiConfig.HTTP_OK:
                    activity.logger.info("Loki health check passed!")
                    return True
        except Exception as e:
            activity.logger.debug(f"Health check failed: {e}")
        
        await asyncio.sleep(LokiConfig.HEALTH_CHECK_INTERVAL)
    
    raise RuntimeError(f"Container not healthy within {LokiConfig.MAX_WAIT_TIME}s")


async def _stop_and_clean_loki_container(client, container):
    """Stop and clean a single Loki container."""
    container_name = container.name
    
    try:
        activity.logger.info(f"Stopping container {container_name}...")
        container.stop(timeout=30)
        container.wait()
        activity.logger.info(f"Container {container_name} stopped")
        
        activity.logger.info(f"Removing container {container_name}...")
        container.remove(force=True)
        activity.logger.info(f"Container {container_name} removed")
        
        await _remove_loki_volumes(client, container)
        await _remove_loki_networks(client, container)
    
    except Exception as e:
        activity.logger.error(f"Failed to stop {container_name}: {e}")
        try:
            container.remove(force=True)
            activity.logger.info(f"Force removed {container_name}")
        except Exception as e2:
            activity.logger.error(f"Force remove failed: {e2}")


async def _remove_loki_volumes(client, container):
    """Remove volumes associated with Loki container."""
    try:
        for mount in container.attrs.get("Mounts", []):
            if mount.get("Name"):
                volume_name = mount["Name"]
                try:
                    volume = client.volumes.get(volume_name)
                    volume.remove(force=True)
                    activity.logger.info(f"Removed volume: {volume_name}")
                except docker.errors.NotFound:
                    pass
                except Exception as e:
                    activity.logger.error(f"Failed to remove volume: {e}")
    except Exception as e:
        activity.logger.error(f"Volume cleanup error: {e}")


async def _remove_loki_networks(client, container):
    """Remove networks associated with Loki container."""
    try:
        networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
        for net_name in networks.keys():
            if net_name not in ["bridge", "host", "none"]:
                try:
                    network = client.networks.get(net_name)
                    network.remove()
                    activity.logger.info(f"Removed network: {net_name}")
                except docker.errors.NotFound:
                    pass
                except Exception as e:
                    activity.logger.error(f"Failed to remove network: {e}")
    except Exception as e:
        activity.logger.error(f"Network cleanup error: {e}")


async def _cleanup_loki_resources(client, service_name):
    """Clean up orphaned Loki resources."""
    try:
        for image in client.images.list():
            for tag in image.tags:
                if service_name in tag:
                    try:
                        client.images.remove(image.id, force=True)
                        activity.logger.info(f"Removed image: {tag}")
                    except Exception as e:
                        activity.logger.error(f"Failed to remove image: {e}")
        
        for network in client.networks.list():
            if service_name in network.name:
                try:
                    network.remove()
                    activity.logger.info(f"Removed network: {network.name}")
                except Exception as e:
                    activity.logger.error(f"Failed to remove network: {e}")
    except Exception as e:
        activity.logger.error(f"Resource cleanup error: {e}")


async def _fetch_loki_logs():
    """Fetch and log Loki container logs."""
    try:
        client = docker.from_env()
        container = client.containers.get(LokiConfig.CONTAINER_NAME)
        logs = container.logs(tail=1000).decode("utf-8", errors="replace")
        activity.logger.error(f"Loki logs:\n{logs}")
    except docker.errors.NotFound:
        activity.logger.error(f"Cannot fetch logs: container not found")
    except Exception as e:
        activity.logger.error(f"Failed to fetch logs: {e}")