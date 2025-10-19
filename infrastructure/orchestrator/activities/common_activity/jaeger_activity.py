import logging
import socket
import time

import docker
from docker.errors import APIError, DockerException, ImageNotFound, NotFound
from temporalio import activity

# Service Access Information:
# UI URL: http://localhost:16686
# OTLP gRPC Collector: localhost:4317
# OTLP HTTP Collector: localhost:4318
# Username: N/A (No authentication by default)
# Password: N/A
# Note: all-in-one includes collector, query service, and UI

logging.basicConfig(level=logging.INFO)

CONFIG = {
    "image_name": "jaegertracing/all-in-one:latest",
    "container_name": "jaeger-development",
    "environment": {
        "COLLECTOR_OTLP_ENABLED": "true",
        "COLLECTOR_ZIPKIN_HOST_PORT": ":9411",
    },
    "ports": {
        "16686/tcp": 16686,  # UI
        "4317/tcp": 4317,  # OTLP gRPC
        "4318/tcp": 4318,  # OTLP HTTP
        "14250/tcp": 14250,  # Model proto
        "14268/tcp": 14268,  # Jaeger thrift
        "9411/tcp": 9411,  # Zipkin
    },
    "volumes": {"jaeger-data": {"bind": "/tmp", "mode": "rw"}},
    "restart_policy": {"Name": "unless-stopped"},
    "network": "observability-network",
    "resources": {"mem_limit": "512m", "cpus": 0.5},
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
async def start_jaeger_container(service_name: str) -> bool:
    logging.info(f"Starting Jaeger for {service_name}")

    required_ports = [16686, 4317, 4318, 14250, 14268, 9411]
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
                        logging.info("Jaeger already running")
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
                    logging.info("Pulling Jaeger image")
                    try:
                        client.images.pull(CONFIG["image_name"])
                        logging.info("Jaeger image pulled successfully")
                    except Exception as e:
                        logging.exception(f"Failed to pull Jaeger image: {e}")
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
    logging.error("All attempts to start Jaeger failed")
    return False
