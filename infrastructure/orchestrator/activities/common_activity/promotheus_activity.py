"""Temporal activities for managing Prometheus monitoring containers.

Activities:
    - start_prometheus_container: Starts the Prometheus container and waits for health
    - stop_prometheus_container: Stops the Prometheus container and cleans up resources
"""

import asyncio
import os
from pathlib import Path
import subprocess
import time

import docker
from temporalio import activity


class PrometheusConfig:
    """Configuration for Prometheus container management."""
    
    CONTAINER_NAME = "prometheus"
    SERVICE_NAME = "prometheus"
    _current_file = Path(__file__)
    PROJECT_ROOT = str(_current_file.parent.parent.parent.parent.parent.resolve())
    SERVICE_DIR = os.path.join(
        PROJECT_ROOT, "infrastructure", "monitoring", "component", "prometheus"
    )
    COMPOSE_FILE = os.path.join(SERVICE_DIR, "prometheus-compose.yaml")
    
    HEALTH_ENDPOINT = "http://localhost:9090/-/healthy"
    READY_ENDPOINT = "http://localhost:9090/-/ready"
    HEALTH_CHECK_TIMEOUT = 5
    HEALTH_CHECK_INTERVAL = 10
    MAX_WAIT_TIME = 120
    MAX_RACE_RETRIES = 3
    
    HTTP_OK = 200


@activity.defn
async def start_prometheus_container(service_name: str) -> bool:
    """Start the Prometheus container and wait until it is healthy."""
    activity.logger.info(f"Starting Prometheus container for service: {service_name}")
    
    try:
        client = docker.from_env()
        race_attempts = 0
        
        while race_attempts < PrometheusConfig.MAX_RACE_RETRIES:
            try:
                container = await _get_or_start_prometheus_container(client)
                return await _wait_for_healthy_prometheus(container)
            except RuntimeError as e:
                race_attempts += 1
                activity.logger.warning(f"Attempt {race_attempts} failed: {e}")
                await asyncio.sleep(2)
        
        await _fetch_prometheus_logs()
        raise RuntimeError("Prometheus failed to become healthy")
    
    except Exception as e:
        activity.logger.error(f"Failed to start Prometheus: {e}")
        await _fetch_prometheus_logs()
        raise


@activity.defn
async def stop_prometheus_container(service_name: str) -> bool:
    """Stop the Prometheus container and clean up resources."""
    activity.logger.info(f"Stopping Prometheus for service: {service_name}")
    
    client = docker.from_env()
    containers_to_stop = []
    
    for container in client.containers.list(all=True):
        if service_name in container.name or PrometheusConfig.CONTAINER_NAME in container.name:
            containers_to_stop.append(container)
            activity.logger.info(f"Found container: {container.name}")
    
    if not containers_to_stop:
        activity.logger.info(f"No containers found for: {service_name}")
        return True
    
    for container in containers_to_stop:
        await _stop_and_clean_prometheus_container(client, container)
    
    await _cleanup_prometheus_resources(client, service_name)
    return True


async def _get_or_start_prometheus_container(client):
    """Get existing Prometheus container or start a new one."""
    try:
        container = client.containers.get(PrometheusConfig.CONTAINER_NAME)
        container.reload()
        
        if container.status == "running":
            activity.logger.info(f"Container {PrometheusConfig.CONTAINER_NAME} is running")
            if await _check_prometheus_health():
                activity.logger.info("Prometheus is healthy!")
                return container
            activity.logger.info("Not healthy, restarting")
            await _start_prometheus_via_compose()
        else:
            activity.logger.info(f"Starting existing container {PrometheusConfig.CONTAINER_NAME}")
            container.start()
    except docker.errors.NotFound:
        activity.logger.info(f"Container not found, starting via docker-compose")
        await _start_prometheus_via_compose()
    
    return client.containers.get(PrometheusConfig.CONTAINER_NAME)


async def _check_prometheus_health() -> bool:
    """Check if Prometheus health endpoint is responding."""
    import urllib.request
    
    try:
        with urllib.request.urlopen(
            PrometheusConfig.HEALTH_ENDPOINT,
            timeout=PrometheusConfig.HEALTH_CHECK_TIMEOUT,
        ) as response:
            if response.status == PrometheusConfig.HTTP_OK:
                # Also check ready endpoint
                with urllib.request.urlopen(
                    PrometheusConfig.READY_ENDPOINT,
                    timeout=PrometheusConfig.HEALTH_CHECK_TIMEOUT,
                ) as ready_response:
                    return ready_response.status == PrometheusConfig.HTTP_OK
    except (urllib.error.URLError, OSError):
        return False
    return False


async def _start_prometheus_via_compose() -> None:
    """Start Prometheus using docker-compose."""
    cmd = [
        "docker-compose",
        "-f", PrometheusConfig.COMPOSE_FILE,
        "up", "-d", PrometheusConfig.SERVICE_NAME,
    ]
    try:
        activity.logger.info(f"Starting via docker-compose: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            cwd=PrometheusConfig.SERVICE_DIR,
        )
        activity.logger.info(f"Start output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Start failed: {e.stderr}")
        raise RuntimeError(f"Failed to start Prometheus: {e}") from e


async def _wait_for_healthy_prometheus(container) -> bool:
    """Wait for Prometheus to become healthy."""
    import urllib.request
    
    start_time = time.time()
    while time.time() - start_time < PrometheusConfig.MAX_WAIT_TIME:
        try:
            container.reload()
            if container.status != "running":
                raise RuntimeError(f"Container stopped (status={container.status})")
            
            # Check both health and ready endpoints
            with urllib.request.urlopen(
                PrometheusConfig.HEALTH_ENDPOINT,
                timeout=PrometheusConfig.HEALTH_CHECK_TIMEOUT,
            ) as response:
                if response.status == PrometheusConfig.HTTP_OK:
                    with urllib.request.urlopen(
                        PrometheusConfig.READY_ENDPOINT,
                        timeout=PrometheusConfig.HEALTH_CHECK_TIMEOUT,
                    ) as ready_response:
                        if ready_response.status == PrometheusConfig.HTTP_OK:
                            activity.logger.info("Prometheus health check passed!")
                            return True
        except Exception as e:
            activity.logger.debug(f"Health check failed: {e}")
        
        await asyncio.sleep(PrometheusConfig.HEALTH_CHECK_INTERVAL)
    
    raise RuntimeError(f"Container not healthy within {PrometheusConfig.MAX_WAIT_TIME}s")


async def _stop_and_clean_prometheus_container(client, container):
    """Stop and clean a single Prometheus container."""
    container_name = container.name
    
    try:
        activity.logger.info(f"Stopping container {container_name}...")
        container.stop(timeout=30)
        container.wait()
        activity.logger.info(f"Container {container_name} stopped")
        
        activity.logger.info(f"Removing container {container_name}...")
        container.remove(force=True)
        activity.logger.info(f"Container {container_name} removed")
        
        await _remove_prometheus_volumes(client, container)
        await _remove_prometheus_networks(client, container)
    
    except Exception as e:
        activity.logger.error(f"Failed to stop {container_name}: {e}")
        try:
            container.remove(force=True)
            activity.logger.info(f"Force removed {container_name}")
        except Exception as e2:
            activity.logger.error(f"Force remove failed: {e2}")


async def _remove_prometheus_volumes(client, container):
    """Remove volumes associated with Prometheus container."""
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
        
        # Check for prometheus-data volume
        try:
            volume = client.volumes.get("prometheus-data")
            volume.remove(force=True)
            activity.logger.info(f"Removed prometheus-data volume")
        except docker.errors.NotFound:
            pass
        except Exception as e:
            activity.logger.error(f"Failed to remove prometheus-data: {e}")
    except Exception as e:
        activity.logger.error(f"Volume cleanup error: {e}")


async def _remove_prometheus_networks(client, container):
    """Remove networks associated with Prometheus container."""
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


async def _cleanup_prometheus_resources(client, service_name):
    """Clean up orphaned Prometheus resources."""
    try:
        for image in client.images.list():
            for tag in image.tags:
                if service_name in tag or "prometheus" in tag.lower():
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


async def _fetch_prometheus_logs():
    """Fetch and log Prometheus container logs."""
    try:
        client = docker.from_env()
        container = client.containers.get(PrometheusConfig.CONTAINER_NAME)
        logs = container.logs(tail=1000).decode("utf-8", errors="replace")
        activity.logger.error(f"Prometheus logs:\n{logs}")
    except docker.errors.NotFound:
        activity.logger.error(f"Cannot fetch logs: container not found")
    except Exception as e:
        activity.logger.error(f"Failed to fetch logs: {e}")