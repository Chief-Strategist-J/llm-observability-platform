"""Temporal activities for managing OpenTelemetry Collector containers.

This module provides Temporal activities to start and stop the OTel Collector
container in the monitoring infrastructure.

Activities:
    - start_otel_container: Starts the OTel Collector container and waits for health
    - stop_otel_container: Stops the OTel Collector container and cleans up resources
"""

import asyncio
import os
from pathlib import Path
import subprocess
import time

import docker
from temporalio import activity


class OtelConfig:
    """Configuration for OTel Collector container management."""
    
    CONTAINER_NAME = "otel-collector"
    SERVICE_NAME = "otel-collector"
    _current_file = Path(__file__)
    PROJECT_ROOT = str(_current_file.parent.parent.parent.parent.parent.resolve())
    SERVICE_DIR = os.path.join(
        PROJECT_ROOT, "infrastructure", "monitoring", "component", "otel"
    )
    COMPOSE_FILE = os.path.join(SERVICE_DIR, "otel-collector-compose.yaml")
    
    HEALTH_ENDPOINT = "http://localhost:8888/metrics"
    HEALTH_CHECK_TIMEOUT = 5
    HEALTH_CHECK_INTERVAL = 10
    MAX_WAIT_TIME = 120
    MAX_RACE_RETRIES = 3
    
    HTTP_OK = 200


@activity.defn
async def start_otel_container(service_name: str) -> bool:
    """Start the OTel Collector container and wait until it is healthy."""
    activity.logger.info(f"Starting OTel Collector container for service: {service_name}")
    
    try:
        await _build_otel_container()
        client = docker.from_env()
        race_attempts = 0
        
        while race_attempts < OtelConfig.MAX_RACE_RETRIES:
            try:
                container = await _get_or_start_otel_container(client)
                return await _wait_for_healthy_otel(container)
            except RuntimeError as e:
                race_attempts += 1
                activity.logger.warning(
                    f"Attempt {race_attempts} failed: {e}"
                )
                await asyncio.sleep(2)
        
        await _fetch_otel_logs()
        raise RuntimeError("OTel Collector failed to become healthy")
    
    except Exception as e:
        activity.logger.error(f"Failed to start OTel Collector: {e}")
        await _fetch_otel_logs()
        raise


@activity.defn
async def stop_otel_container(service_name: str) -> bool:
    """Stop the OTel Collector container and clean up resources."""
    activity.logger.info(f"Stopping OTel Collector for service: {service_name}")
    
    client = docker.from_env()
    containers_to_stop = []
    
    for container in client.containers.list(all=True):
        if service_name in container.name or OtelConfig.CONTAINER_NAME in container.name:
            containers_to_stop.append(container)
            activity.logger.info(f"Found container: {container.name}")
    
    if not containers_to_stop:
        activity.logger.info(f"No containers found for: {service_name}")
        return True
    
    for container in containers_to_stop:
        await _stop_and_clean_otel_container(client, container)
    
    await _cleanup_otel_resources(client, service_name)
    return True


async def _build_otel_container() -> None:
    """Build the OTel Collector container using docker-compose."""
    cmd = [
        "docker-compose",
        "-f", OtelConfig.COMPOSE_FILE,
        "build", OtelConfig.SERVICE_NAME,
    ]
    try:
        activity.logger.info(f"Building OTel Collector: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            cwd=OtelConfig.SERVICE_DIR,
        )
        activity.logger.info(f"Build output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Build failed: {e.stderr}")
        raise RuntimeError(f"Failed to build OTel Collector: {e}") from e


async def _get_or_start_otel_container(client):
    """Get existing OTel container or start a new one."""
    try:
        container = client.containers.get(OtelConfig.CONTAINER_NAME)
        container.reload()
        
        if container.status == "running":
            activity.logger.info(f"Container {OtelConfig.CONTAINER_NAME} is running")
            if await _check_otel_health():
                activity.logger.info("OTel Collector is healthy!")
                return container
            activity.logger.info("Not healthy, restarting")
            await _start_otel_via_compose()
        else:
            activity.logger.info(f"Starting existing container {OtelConfig.CONTAINER_NAME}")
            container.start()
    except docker.errors.NotFound:
        activity.logger.info(f"Container not found, starting via docker-compose")
        await _start_otel_via_compose()
    
    return client.containers.get(OtelConfig.CONTAINER_NAME)


async def _check_otel_health() -> bool:
    """Check if OTel Collector health endpoint is responding."""
    import urllib.request
    
    try:
        with urllib.request.urlopen(
            OtelConfig.HEALTH_ENDPOINT,
            timeout=OtelConfig.HEALTH_CHECK_TIMEOUT,
        ) as response:
            return response.status == OtelConfig.HTTP_OK
    except (urllib.error.URLError, OSError):
        return False


async def _start_otel_via_compose() -> None:
    """Start OTel Collector using docker-compose."""
    cmd = [
        "docker-compose",
        "-f", OtelConfig.COMPOSE_FILE,
        "up", "-d", OtelConfig.SERVICE_NAME,
    ]
    try:
        activity.logger.info(f"Starting via docker-compose: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            cwd=OtelConfig.SERVICE_DIR,
        )
        activity.logger.info(f"Start output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Start failed: {e.stderr}")
        raise RuntimeError(f"Failed to start OTel Collector: {e}") from e


async def _wait_for_healthy_otel(container) -> bool:
    """Wait for OTel Collector to become healthy."""
    import urllib.request
    
    start_time = time.time()
    while time.time() - start_time < OtelConfig.MAX_WAIT_TIME:
        try:
            container.reload()
            if container.status != "running":
                raise RuntimeError(f"Container stopped (status={container.status})")
            
            with urllib.request.urlopen(
                OtelConfig.HEALTH_ENDPOINT,
                timeout=OtelConfig.HEALTH_CHECK_TIMEOUT,
            ) as response:
                if response.status == OtelConfig.HTTP_OK:
                    activity.logger.info("OTel Collector health check passed!")
                    return True
        except Exception as e:
            activity.logger.debug(f"Health check failed: {e}")
        
        await asyncio.sleep(OtelConfig.HEALTH_CHECK_INTERVAL)
    
    raise RuntimeError(f"Container not healthy within {OtelConfig.MAX_WAIT_TIME}s")


async def _stop_and_clean_otel_container(client, container):
    """Stop and clean a single OTel container."""
    container_name = container.name
    
    try:
        activity.logger.info(f"Stopping container {container_name}...")
        container.stop(timeout=30)
        container.wait()
        activity.logger.info(f"Container {container_name} stopped")
        
        activity.logger.info(f"Removing container {container_name}...")
        container.remove(force=True)
        activity.logger.info(f"Container {container_name} removed")
        
        await _remove_otel_volumes(client, container)
        await _remove_otel_networks(client, container)
    
    except Exception as e:
        activity.logger.error(f"Failed to stop {container_name}: {e}")
        try:
            container.remove(force=True)
            activity.logger.info(f"Force removed {container_name}")
        except Exception as e2:
            activity.logger.error(f"Force remove failed: {e2}")


async def _remove_otel_volumes(client, container):
    """Remove volumes associated with OTel container."""
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


async def _remove_otel_networks(client, container):
    """Remove networks associated with OTel container."""
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


async def _cleanup_otel_resources(client, service_name):
    """Clean up orphaned OTel resources."""
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


async def _fetch_otel_logs():
    """Fetch and log OTel Collector container logs."""
    try:
        client = docker.from_env()
        container = client.containers.get(OtelConfig.CONTAINER_NAME)
        logs = container.logs(tail=1000).decode("utf-8", errors="replace")
        activity.logger.error(f"OTel logs:\n{logs}")
    except docker.errors.NotFound:
        activity.logger.error(f"Cannot fetch logs: container not found")
    except Exception as e:
        activity.logger.error(f"Failed to fetch logs: {e}")