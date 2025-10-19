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
import logging
from pathlib import Path
import socket
import subprocess
import time

import docker
from docker.errors import APIError, BuildError, DockerException, NotFound
from temporalio import activity

logging.basicConfig(level=logging.INFO)

CONFIG = {
    "image_name": "ai-proxy-service:custom",
    "container_name": "ai-proxy-api",
    "dockerfile_path": "Dockerfile",
    "build_context": "./ai-proxy-service",
    "ports": {"8001/tcp": 8001},
    "volumes": {"ai-proxy-data": {"bind": "/app/data", "mode": "rw"}},
    "restart_policy": {"Name": "unless-stopped"},
    "network": "monitoring-bridge",
    "resources": {"mem_limit": "512m", "cpus": 0.5},
    "start_timeout": 30,
    "stop_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 5,
    "user": "472",
    "health_endpoint": "http://localhost:8001/health",
    "health_check_timeout": 5,
    "health_check_interval": 10,
    "max_wait_time": 300,
    "max_race_retries": 3,
    "project_root": str(Path(__file__).parent.parent.parent.parent.resolve()),
    "service_dir": str(
        Path(__file__).parent.parent.parent.parent
        / "infrastructure"
        / "services"
        / "ai-proxy-service"
    ),
    "compose_file": str(
        Path(__file__).parent.parent.parent.parent
        / "infrastructure"
        / "services"
        / "ai-proxy-service"
        / "ai-proxy-service.docker-compose.yml"
    ),
    "service_name": "api",
}

try:
    client = docker.from_env()
except DockerException as e:
    raise RuntimeError(f"Docker daemon unreachable: {e}")


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def ensure_network():
    try:
        client.networks.get(CONFIG["network"])
        logging.info(f"Network {CONFIG['network']} exists")
    except NotFound:
        logging.info(f"Network {CONFIG['network']} not found, creating")
        client.networks.create(CONFIG["network"])
        logging.info(f"Network {CONFIG['network']} created")


def build_image():
    try:
        logging.info("Building AI proxy image")
        client.images.build(
            path=CONFIG["build_context"],
            dockerfile=CONFIG["dockerfile_path"],
            tag=CONFIG["image_name"],
        )
        logging.info("Image build complete")
    except BuildError as e:
        logging.exception(f"Failed to build image: {e}")
        raise


def cleanup_dead_container(container):
    if container.status == "dead":
        logging.warning("Container in dead state, removing")
        container.remove(force=True)
        return True
    return False


def wait_for_dependencies():
    # AI proxy doesn't have dependencies like loki/promtail
    pass


@activity.defn
async def start_app_container(service_name: str) -> bool:
    """
    Start the ai-proxy-service container and wait until it is healthy.
    """
    logging.info(f"Starting AI proxy container for service: {service_name}")

    if is_port_in_use(8001):
        logging.error("Port 8001 already in use")
        return False

    # Build via docker-compose first
    await _build_container_via_compose()

    ensure_network()

    for attempt in range(CONFIG["retry_attempts"]):
        try:
            try:
                container = client.containers.get(CONFIG["container_name"])
                if cleanup_dead_container(container):
                    container = None

                if container:
                    if container.status == "running":
                        if await _check_container_health():
                            logging.info("AI proxy already running and healthy")
                            return True
                        logging.info("Not healthy, restarting")
                        await _start_container_via_compose()
                    elif container.status in [
                        "exited",
                        "created",
                        "paused",
                        "restarting",
                    ]:
                        logging.info(
                            f"Starting existing container (status: {container.status})"
                        )
                        container.start()
                        return await _wait_for_healthy_container(container)
            except NotFound:
                logging.info("Container not found, starting via docker-compose")
                await _start_container_via_compose()

            container = client.containers.get(CONFIG["container_name"])
            return await _wait_for_healthy_container(container)

        except (DockerException, APIError) as e:
            logging.exception(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(CONFIG["retry_delay"])

    await _fetch_container_logs()
    logging.error("All attempts to start AI proxy failed")
    return False


@activity.defn
async def stop_app_container(service_name: str) -> bool:
    """
    Stop the ai-proxy-service container and clean up resources.
    """
    logging.info(f"Stopping AI proxy for service: {service_name}")

    for attempt in range(CONFIG["retry_attempts"]):
        try:
            try:
                container = client.containers.get(CONFIG["container_name"])
            except NotFound:
                logging.info("AI proxy container not found")
                return True

            if container.status in ["running", "restarting"]:
                logging.info(f"Stopping container (status: {container.status})")
                container.stop(timeout=CONFIG["stop_timeout"])
            container.remove()
            logging.info("AI proxy stopped and removed successfully")
            return True
        except (DockerException, APIError) as e:
            logging.exception(f"Attempt {attempt + 1} to stop AI proxy failed: {e}")
            time.sleep(CONFIG["retry_delay"])
    logging.error("All attempts to stop AI proxy failed")
    return False


async def _build_container_via_compose() -> None:
    """
    Build the container using docker-compose.
    """
    cmd = [
        "docker-compose",
        "-f",
        CONFIG["compose_file"],
        "build",
        CONFIG["service_name"],
    ]
    try:
        logging.info(f"Building container: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=CONFIG["service_dir"],
        )
        logging.info(f"Build output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logging.exception(f"Build failed: {e.stderr}")
        raise RuntimeError(f"Failed to build container: {e}") from e


async def _start_container_via_compose() -> None:
    """
    Start the ai-proxy-service using docker-compose.
    """
    cmd = [
        "docker-compose",
        "-f",
        CONFIG["compose_file"],
        "up",
        "-d",
        CONFIG["service_name"],
    ]
    try:
        logging.info(f"Starting via docker-compose: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=CONFIG["service_dir"],
        )
        logging.info(f"Start output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logging.exception(f"Start failed: {e.stderr}")
        raise RuntimeError(f"Failed to start container: {e}") from e


async def _check_container_health() -> bool:
    """
    Check if container health endpoint is responding.
    """
    import urllib.request

    try:
        with urllib.request.urlopen(
            CONFIG["health_endpoint"],
            timeout=CONFIG["health_check_timeout"],
        ) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError):
        return False


async def _wait_for_healthy_container(container) -> bool:
    """
    Wait for container to become healthy.
    """
    import urllib.request

    start_time = time.time()
    while time.time() - start_time < CONFIG["max_wait_time"]:
        try:
            container.reload()
            if container.status != "running":
                raise RuntimeError(f"Container stopped (status={container.status})")

            with urllib.request.urlopen(
                CONFIG["health_endpoint"],
                timeout=CONFIG["health_check_timeout"],
            ) as response:
                if response.status == 200:
                    logging.info("AI proxy health check passed!")
                    return True
        except Exception as e:
            logging.debug(f"Health check failed: {e}")

        await asyncio.sleep(CONFIG["health_check_interval"])

    raise RuntimeError(f"Container not healthy within {CONFIG['max_wait_time']}s")


async def _fetch_container_logs():
    """
    Fetch and log container logs.
    """
    try:
        container = client.containers.get(CONFIG["container_name"])
        logs = container.logs(tail=1000).decode("utf-8", errors="replace")
        logging.error(f"AI proxy logs:\n{logs}")
    except NotFound:
        logging.exception("Cannot fetch logs: container not found")
    except Exception as e:
        logging.exception(f"Failed to fetch logs: {e}")
