"""Temporal activities for managing Promtail log shipper containers.

Activities:
    - start_promtail_container: Starts the Promtail container
    - stop_promtail_container: Stops the Promtail container and cleans up resources
"""

import asyncio
import os
from pathlib import Path
import subprocess
import time

import docker
from temporalio import activity


class PromtailConfig:
    """Configuration for Promtail container management."""
    
    CONTAINER_NAME = "promtail"
    SERVICE_NAME = "promtail"
    _current_file = Path(__file__)
    PROJECT_ROOT = str(_current_file.parent.parent.parent.parent.parent.resolve())
    SERVICE_DIR = os.path.join(
        PROJECT_ROOT, "infrastructure", "monitoring", "component", "loki"
    )
    COMPOSE_FILE = os.path.join(SERVICE_DIR, "logger-loki-compose.yaml")
    
    # Promtail doesn't have a standard health endpoint, check if container is running
    HEALTH_CHECK_TIMEOUT = 5
    HEALTH_CHECK_INTERVAL = 5
    MAX_WAIT_TIME = 60
    MAX_RACE_RETRIES = 3


@activity.defn
async def start_promtail_container(service_name: str) -> bool:
    """Start the Promtail container."""
    activity.logger.info(f"Starting Promtail container for service: {service_name}")
    
    try:
        await _build_promtail_container()
        client = docker.from_env()
        race_attempts = 0
        
        while race_attempts < PromtailConfig.MAX_RACE_RETRIES:
            try:
                container = await _get_or_start_promtail_container(client)
                return await _wait_for_running_promtail(container)
            except RuntimeError as e:
                race_attempts += 1
                activity.logger.warning(f"Attempt {race_attempts} failed: {e}")
                await asyncio.sleep(2)
        
        await _fetch_promtail_logs()
        raise RuntimeError("Promtail failed to start")
    
    except Exception as e:
        activity.logger.error(f"Failed to start Promtail: {e}")
        await _fetch_promtail_logs()
        raise


@activity.defn
async def stop_promtail_container(service_name: str) -> bool:
    """Stop the Promtail container and clean up resources."""
    activity.logger.info(f"Stopping Promtail for service: {service_name}")
    
    client = docker.from_env()
    containers_to_stop = []
    
    for container in client.containers.list(all=True):
        if service_name in container.name or PromtailConfig.CONTAINER_NAME in container.name:
            containers_to_stop.append(container)
            activity.logger.info(f"Found container: {container.name}")
    
    if not containers_to_stop:
        activity.logger.info(f"No containers found for: {service_name}")
        return True
    
    for container in containers_to_stop:
        await _stop_and_clean_promtail_container(client, container)
    
    await _cleanup_promtail_resources(client, service_name)
    return True


async def _build_promtail_container() -> None:
    """Build the Promtail container using docker-compose."""
    cmd = [
        "docker-compose",
        "-f", PromtailConfig.COMPOSE_FILE,
        "build", PromtailConfig.SERVICE_NAME,
    ]
    try:
        activity.logger.info(f"Building Promtail: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            cwd=PromtailConfig.SERVICE_DIR,
        )
        activity.logger.info(f"Build output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Build failed: {e.stderr}")
        raise RuntimeError(f"Failed to build Promtail: {e}") from e


async def _get_or_start_promtail_container(client):
    """Get existing Promtail container or start a new one."""
    try:
        container = client.containers.get(PromtailConfig.CONTAINER_NAME)
        container.reload()
        
        if container.status == "running":
            activity.logger.info(f"Container {PromtailConfig.CONTAINER_NAME} is running")
            return container
        else:
            activity.logger.info(f"Starting existing container {PromtailConfig.CONTAINER_NAME}")
            container.start()
    except docker.errors.NotFound:
        activity.logger.info(f"Container not found, starting via docker-compose")
        await _start_promtail_via_compose()
    
    return client.containers.get(PromtailConfig.CONTAINER_NAME)


async def _start_promtail_via_compose() -> None:
    """Start Promtail using docker-compose."""
    cmd = [
        "docker-compose",
        "-f", PromtailConfig.COMPOSE_FILE,
        "up", "-d", PromtailConfig.SERVICE_NAME,
    ]
    try:
        activity.logger.info(f"Starting via docker-compose: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            cwd=PromtailConfig.SERVICE_DIR,
        )
        activity.logger.info(f"Start output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Start failed: {e.stderr}")
        raise RuntimeError(f"Failed to start Promtail: {e}") from e


async def _wait_for_running_promtail(container) -> bool:
    """Wait for Promtail to be running and stable."""
    start_time = time.time()
    while time.time() - start_time < PromtailConfig.MAX_WAIT_TIME:
        try:
            container.reload()
            if container.status == "running":
                # Wait a bit more to ensure it stays running
                await asyncio.sleep(5)
                container.reload()
                if container.status == "running":
                    activity.logger.info("Promtail is running!")
                    return True
            else:
                raise RuntimeError(f"Container status: {container.status}")
        except Exception as e:
            activity.logger.debug(f"Status check failed: {e}")
        
        await asyncio.sleep(PromtailConfig.HEALTH_CHECK_INTERVAL)
    
    raise RuntimeError(f"Container not running within {PromtailConfig.MAX_WAIT_TIME}s")


async def _stop_and_clean_promtail_container(client, container):
    """Stop and clean a single Promtail container."""
    container_name = container.name
    
    try:
        activity.logger.info(f"Stopping container {container_name}...")
        container.stop(timeout=30)
        container.wait()
        activity.logger.info(f"Container {container_name} stopped")
        
        activity.logger.info(f"Removing container {container_name}...")
        container.remove(force=True)
        activity.logger.info(f"Container {container_name} removed")
        
        await _remove_promtail_volumes(client, container)
        await _remove_promtail_networks(client, container)
    
    except Exception as e:
        activity.logger.error(f"Failed to stop {container_name}: {e}")
        try:
            container.remove(force=True)
            activity.logger.info(f"Force removed {container_name}")
        except Exception as e2:
            activity.logger.error(f"Force remove failed: {e2}")


async def _remove_promtail_volumes(client, container):
    """Remove volumes associated with Promtail container."""
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


async def _remove_promtail_networks(client, container):
    """Remove networks associated with Promtail container."""
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


async def _cleanup_promtail_resources(client, service_name):
    """Clean up orphaned Promtail resources."""
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


async def _fetch_promtail_logs():
    """Fetch and log Promtail container logs."""
    try:
        client = docker.from_env()
        container = client.containers.get(PromtailConfig.CONTAINER_NAME)
        logs = container.logs(tail=1000).decode("utf-8", errors="replace")
        activity.logger.error(f"Promtail logs:\n{logs}")
    except docker.errors.NotFound:
        activity.logger.error(f"Cannot fetch logs: container not found")
    except Exception as e:
        activity.logger.error(f"Failed to fetch logs: {e}")