#!/usr/bin/env python3
"""Grafana start activity - handles starting the Grafana container."""

import logging
import socket
import time

import docker
from docker.errors import APIError, DockerException, ImageNotFound, NotFound
from temporalio import activity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Docker client
try:
    client = docker.from_env()
except DockerException as e:
    raise RuntimeError(f"Docker daemon unreachable: {e}")


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def ensure_network(name: str):
    """
    Create network if it doesn't exist.
    """
    try:
        net = client.networks.get(name)
        logger.info("Network %s exists", name)
        return net
    except NotFound:
        logger.info("Network %s not found, creating", name)
        net = client.networks.create(name)
        logger.info("Network %s created", name)
        return net


def cleanup_dead_container(container):
    if container.status == "dead":
        logger.warning("Container in dead state, removing")
        container.remove(force=True)
        return True
    return False


def get_container(name: str):
    try:
        return client.containers.get(name)
    except NotFound:
        return None


@activity.defn
async def start_grafana_container(service_name: str) -> bool:
    """
    Start the Grafana container.
    """
    logger.info(f"Starting Grafana for {service_name}")

    # Configuration constants
    CONTAINER_CONFIG = {
        "image_name": "grafana/grafana:latest",
        "container_name": "grafana-development",
        "environment": {
            "GF_SECURITY_ADMIN_USER": "admin",
            "GF_SECURITY_ADMIN_PASSWORD": "SuperSecret123!",
            "GF_USERS_ALLOW_SIGN_UP": "false",
        },
        "ports": {"3000/tcp": 31001},
        "volumes": {"grafana-data": {"bind": "/var/lib/grafana", "mode": "rw"}},
        "restart_policy": {"Name": "unless-stopped"},
        "network": "monitoring-bridge",
        "resources": {"mem_limit": "256m", "cpus": 0.5},
        "start_timeout": 30,
        "stop_timeout": 30,
        "retry_attempts": 3,
        "retry_delay": 5,
    }

    if is_port_in_use(31001):
        logger.error("Port 31001 already in use")
        return False

    # Make sure the declared network exists
    try:
        ensure_network(CONTAINER_CONFIG["network"])
    except Exception as e:
        logger.exception("Failed to ensure network: %s", e)
        # continue: we try to start container anyway

    for attempt in range(CONTAINER_CONFIG["retry_attempts"]):
        try:
            try:
                container = client.containers.get(CONTAINER_CONFIG["container_name"])
                if cleanup_dead_container(container):
                    container = None

                if container:
                    if container.status == "running":
                        logger.info("Grafana already running")
                        return True
                    if container.status in [
                        "exited",
                        "created",
                        "paused",
                        "restarting",
                    ]:
                        logger.info(
                            f"Starting existing container (status: {container.status})"
                        )
                        container.start()
                        return True
            except NotFound:
                logger.info("Container not found, creating new one")
                try:
                    client.images.get(CONTAINER_CONFIG["image_name"])
                    logger.info("Image already exists, skipping pull")
                except ImageNotFound:
                    logger.info("Pulling Grafana image")
                    try:
                        client.images.pull(CONTAINER_CONFIG["image_name"])
                        logger.info("Grafana image pulled successfully")
                    except Exception as e:
                        logger.exception(f"Failed to pull Grafana image: {e}")
                        return False

                # Create the container
                client.containers.run(
                    image=CONTAINER_CONFIG["image_name"],
                    name=CONTAINER_CONFIG["container_name"],
                    environment=CONTAINER_CONFIG["environment"],
                    ports=CONTAINER_CONFIG["ports"],
                    volumes=CONTAINER_CONFIG["volumes"],
                    restart_policy=CONTAINER_CONFIG["restart_policy"],
                    network=CONTAINER_CONFIG["network"],
                    detach=True,
                    mem_limit=CONTAINER_CONFIG["resources"]["mem_limit"],
                    nano_cpus=int(CONTAINER_CONFIG["resources"]["cpus"] * 1e9),
                )
                logger.info("Container started successfully")
            return True
        except (DockerException, APIError) as e:
            logger.exception(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(CONTAINER_CONFIG["retry_delay"])
    logger.error("All attempts to start Grafana failed")
    return False
