import logging
import socket
import time

import docker
from docker.errors import APIError, DockerException, ImageNotFound, NotFound
from temporalio import activity

logging.basicConfig(level=logging.INFO)

CONFIG = {
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


def cleanup_dead_container(container):
    if container.status == "dead":
        logging.warning("Container in dead state, removing")
        container.remove(force=True)
        return True
    return False


@activity.defn
async def start_grafana_container(service_name: str) -> bool:
    logging.info(f"Starting Grafana for {service_name}")

    if is_port_in_use(31001):
        logging.error("Port 31001 already in use")
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
                        logging.info("Grafana already running")
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
                    logging.info("Image already exists, skipping build")
                except ImageNotFound:
                    logging.info("Pulling Grafana image")
                    try:
                        client.images.pull(CONFIG["image_name"])
                        logging.info("Grafana image pulled successfully")
                    except Exception as e:
                        logging.exception(f"Failed to pull Grafana image: {e}")
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
    logging.error("All attempts to start Grafana failed")
    return False
