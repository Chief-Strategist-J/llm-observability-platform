import logging
import socket
import time

import docker
from docker.errors import APIError, DockerException, ImageNotFound, NotFound
from temporalio import activity

# Service Access Information:
# Browser UI: http://localhost:7474
# Bolt Protocol: bolt://localhost:7687
# Username: neo4j (default)
# Password: Neo4jPassword123! (set via NEO4J_AUTH)
# Note: Change password in production for security

logging.basicConfig(level=logging.INFO)

CONFIG = {
    "image_name": "neo4j:latest",
    "container_name": "neo4j-development",
    "environment": {
        "NEO4J_AUTH": "neo4j/Neo4jPassword123!",
        "NEO4J_ACCEPT_LICENSE_AGREEMENT": "yes",
        "NEO4J_dbms_memory_pagecache_size": "512M",
        "NEO4J_dbms_memory_heap_initial__size": "512M",
        "NEO4J_dbms_memory_heap_max__size": "512M",
    },
    "ports": {"7474/tcp": 7474, "7687/tcp": 7687},  # HTTP  # Bolt
    "volumes": {
        "neo4j-data": {"bind": "/data", "mode": "rw"},
        "neo4j-logs": {"bind": "/logs", "mode": "rw"},
        "neo4j-import": {"bind": "/var/lib/neo4j/import", "mode": "rw"},
        "neo4j-plugins": {"bind": "/plugins", "mode": "rw"},
    },
    "restart_policy": {"Name": "unless-stopped"},
    "network": "data-network",
    "resources": {"mem_limit": "1g", "cpus": 1.0},
    "start_timeout": 30,
    "stop_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 5,
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
        client.networks.create(CONFIG["network"], driver="bridge")
        logging.info(f"Network {CONFIG['network']} created")


def cleanup_dead_container(container):
    if container.status == "dead":
        logging.warning("Container in dead state, removing")
        container.remove(force=True)
        return True
    return False


@activity.defn
async def start_neo4j_container(service_name: str) -> bool:
    logging.info(f"Starting Neo4j for {service_name}")

    required_ports = [7474, 7687]
    for port in required_ports:
        if is_port_in_use(port):
            logging.error(f"Port {port} already in use")
            return False

    ensure_network()

    for attempt in range(CONFIG["retry_attempts"]):
        try:
            try:
                container = client.containers.get(CONFIG["container_name"])
                if cleanup_dead_container(container):
                    container = None

                if container:
                    if container.status == "running":
                        logging.info("Neo4j already running")
                        return True
                    if container.status in [
                        "exited",
                        "created",
                        "paused",
                        "restarting",
                    ]:
                        logging.info(
                            f"Starting existing container (status: {container.status})"
                        )
                        container.start()
                        return True
            except NotFound:
                logging.info("Container not found, creating new one")
                try:
                    client.images.get(CONFIG["image_name"])
                    logging.info("Image already exists, skipping pull")
                except ImageNotFound:
                    logging.info("Pulling Neo4j image")
                    try:
                        client.images.pull(CONFIG["image_name"])
                        logging.info("Neo4j image pulled successfully")
                    except Exception as e:
                        logging.exception(f"Failed to pull Neo4j image: {e}")
                        return False

                client.containers.run(
                    image=CONFIG["image_name"],
                    name=CONFIG["container_name"],
                    environment=CONFIG["environment"],
                    ports=CONFIG["ports"],
                    volumes=CONFIG["volumes"],
                    restart_policy=CONFIG["restart_policy"],
                    network=CONFIG["network"],
                    detach=True,
                    mem_limit=CONFIG["resources"]["mem_limit"],
                    nano_cpus=int(CONFIG["resources"]["cpus"] * 1e9),
                )
                logging.info("Container started successfully")
            return True
        except (DockerException, APIError) as e:
            logging.exception(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(CONFIG["retry_delay"])
    logging.error("All attempts to start Neo4j failed")
    return False
