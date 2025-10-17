"""Temporal activities for managing Grafana visualization containers.

Activities:
    - start_grafana_container: Starts the Grafana container and waits for health
    - stop_grafana_container: Stops the Grafana container and cleans up resources
"""

import asyncio
import os
from pathlib import Path
import subprocess
import time

import docker
from temporalio import activity


class GrafanaConfig:
    """Configuration for Grafana container management."""
    
    CONTAINER_NAME = "grafana-development"
    SERVICE_NAME = "grafana"
    _current_file = Path(__file__)
    PROJECT_ROOT = str(_current_file.parent.parent.parent.parent.parent.resolve())
    SERVICE_DIR = os.path.join(
        PROJECT_ROOT, "infrastructure", "monitoring", "component", "grafana"
    )
    COMPOSE_FILE = os.path.join(SERVICE_DIR, "dashboard-grafana-compose.yaml")
    
    HEALTH_ENDPOINT = "http://localhost:31001/api/health"
    HEALTH_CHECK_TIMEOUT = 5
    HEALTH_CHECK_INTERVAL = 10
    MAX_WAIT_TIME = 120
    MAX_RACE_RETRIES = 3
    
    HTTP_OK = 200


@activity.defn
async def start_grafana_container(service_name: str) -> bool:
    """Start the Grafana container and wait until it is healthy."""
    activity.logger.info(f"Starting Grafana container for service: {service_name}")
    
    try:
        await _build_grafana_container()
        client = docker.from_env()
        race_attempts = 0
        
        while race_attempts < GrafanaConfig.MAX_RACE_RETRIES:
            try:
                container = await _get_or_start_grafana_container(client)
                return await _wait_for_healthy_grafana(container)
            except RuntimeError as e:
                race_attempts += 1
                activity.logger.warning(f"Attempt {race_attempts} failed: {e}")
                await asyncio.sleep(2)
        
        await _fetch_grafana_logs()
        raise RuntimeError("Grafana failed to become healthy")
    
    except Exception as e:
        activity.logger.error(f"Failed to start Grafana: {e}")
        await _fetch_grafana_logs()
        raise


@activity.defn
async def stop_grafana_container(service_name: str) -> bool:
    """Stop the Grafana container and clean up resources."""
    activity.logger.info(f"Stopping Grafana for service: {service_name}")
    
    client = docker.from_env()
    containers_to_stop = []
    
    for container in client.containers.list(all=True):
        if service_name in container.name or GrafanaConfig.CONTAINER_NAME in container.name:
            containers_to_stop.append(container)
            activity.logger.info(f"Found container: {container.name}")
    
    if not containers_to_stop:
        activity.logger.info(f"No containers found for: {service_name}")
        return True
    
    for container in containers_to_stop:
        await _stop_and_clean_grafana_container(client, container)
    
    await _cleanup_grafana_resources(client, service_name)
    return True


async def _build_grafana_container() -> None:
    """Build the Grafana container using docker-compose."""
    cmd = [
        "docker-compose",
        "-f", GrafanaConfig.COMPOSE_FILE,
        "build", GrafanaConfig.SERVICE_NAME,
    ]
    try:
        activity.logger.info(f"Building Grafana: {' '.join(cmd)}")
        activity.logger.info(f"SERVICE_DIR: {GrafanaConfig.SERVICE_DIR}")
        activity.logger.info(f"COMPOSE_FILE: {GrafanaConfig.COMPOSE_FILE}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            cwd=GrafanaConfig.SERVICE_DIR,
        )
        activity.logger.info(f"Build output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Build failed: {e.stderr}")
        raise RuntimeError(f"Failed to build Grafana: {e}") from e


async def _get_or_start_grafana_container(client):
    """Get existing Grafana container or start a new one."""
    try:
        container = client.containers.get(GrafanaConfig.CONTAINER_NAME)
        container.reload()
        
        if container.status == "running":
            activity.logger.info(f"Container {GrafanaConfig.CONTAINER_NAME} is running")
            if await _check_grafana_health():
                activity.logger.info("Grafana is healthy!")
                return container
            activity.logger.info("Not healthy, restarting")
            await _start_grafana_via_compose()
        else:
            activity.logger.info(f"Starting existing container {GrafanaConfig.CONTAINER_NAME}")
            container.start()
    except docker.errors.NotFound:
        activity.logger.info(f"Container not found, starting via docker-compose")
        await _start_grafana_via_compose()
    
    return client.containers.get(GrafanaConfig.CONTAINER_NAME)


async def _check_grafana_health() -> bool:
    """Check if Grafana health endpoint is responding."""
    import urllib.request
    
    try:
        with urllib.request.urlopen(
            GrafanaConfig.HEALTH_ENDPOINT,
            timeout=GrafanaConfig.HEALTH_CHECK_TIMEOUT,
        ) as response:
            return response.status == GrafanaConfig.HTTP_OK
    except (urllib.error.URLError, OSError):
        return False


async def _start_grafana_via_compose() -> None:
    """Start Grafana using docker-compose."""
    cmd = [
        "docker-compose",
        "-f", GrafanaConfig.COMPOSE_FILE,
        "up", "-d", GrafanaConfig.SERVICE_NAME,
    ]
    try:
        activity.logger.info(f"Starting via docker-compose: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            cwd=GrafanaConfig.SERVICE_DIR,
        )
        activity.logger.info(f"Start output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Start failed: {e.stderr}")
        raise RuntimeError(f"Failed to start Grafana: {e}") from e


async def _wait_for_healthy_grafana(container) -> bool:
    """Wait for Grafana to become healthy."""
    import urllib.request
    
    start_time = time.time()
    while time.time() - start_time < GrafanaConfig.MAX_WAIT_TIME:
        try:
            container.reload()
            if container.status != "running":
                raise RuntimeError(f"Container stopped (status={container.status})")
            
            with urllib.request.urlopen(
                GrafanaConfig.HEALTH_ENDPOINT,
                timeout=GrafanaConfig.HEALTH_CHECK_TIMEOUT,
            ) as response:
                if response.status == GrafanaConfig.HTTP_OK:
                    activity.logger.info("Grafana health check passed!")
                    return True
        except Exception as e:
            activity.logger.debug(f"Health check failed: {e}")
        
        await asyncio.sleep(GrafanaConfig.HEALTH_CHECK_INTERVAL)
    
    raise RuntimeError(f"Container not healthy within {GrafanaConfig.MAX_WAIT_TIME}s")


async def _stop_and_clean_grafana_container(client, container):
    """Stop and clean a single Grafana container."""
    container_name = container.name
    
    try:
        activity.logger.info(f"Stopping container {container_name}...")
        container.stop(timeout=30)
        container.wait()
        activity.logger.info(f"Container {container_name} stopped")
        
        activity.logger.info(f"Removing container {container_name}...")
        container.remove(force=True)
        activity.logger.info(f"Container {container_name} removed")
        
        await _remove_grafana_volumes(client, container)
        await _remove_grafana_networks(client, container)
    
    except Exception as e:
        activity.logger.error(f"Failed to stop {container_name}: {e}")
        try:
            container.remove(force=True)
            activity.logger.info(f"Force removed {container_name}")
        except Exception as e2:
            activity.logger.error(f"Force remove failed: {e2}")


async def _remove_grafana_volumes(client, container):
    """Remove volumes associated with Grafana container."""
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


async def _remove_grafana_networks(client, container):
    """Remove networks associated with Grafana container."""
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


async def _cleanup_grafana_resources(client, service_name):
    """Clean up orphaned Grafana resources."""
    try:
        for image in client.images.list():
            for tag in image.tags:
                if service_name in tag or "grafana" in tag.lower():
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


async def _fetch_grafana_logs():
    """Fetch and log Grafana container logs."""
    try:
        client = docker.from_env()
        container = client.containers.get(GrafanaConfig.CONTAINER_NAME)
        logs = container.logs(tail=1000).decode("utf-8", errors="replace")
        activity.logger.error(f"Grafana logs:\n{logs}")
    except docker.errors.NotFound:
        activity.logger.error(f"Cannot fetch logs: container not found")
    except Exception as e:
        activity.logger.error(f"Failed to fetch logs: {e}")