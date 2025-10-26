import logging
import socket
import time

import docker
from docker.errors import APIError, DockerException, ImageNotFound, NotFound
from temporalio import activity

# Service Access Information:
# OTLP gRPC Receiver: localhost:4317
# OTLP HTTP Receiver: localhost:4318
# Health Check: http://localhost:13133
# Metrics: http://localhost:8888/metrics
# Prometheus Metrics: http://localhost:8889/metrics
# Username: N/A
# Password: N/A
# Purpose: Collects telemetry data (traces, metrics, logs) and exports to observability stack

logging.basicConfig(level=logging.INFO)

CONFIG = {
    "image_name": "otel/opentelemetry-collector-contrib:latest",
    "container_name": "opentelemetry-collector-development",
    "environment": {
        "OTEL_LOG_LEVEL": "INFO",
    },
    "ports": {
        "4317/tcp": 4317,  # OTLP gRPC receiver
        "4318/tcp": 4318,  # OTLP HTTP receiver
        "13133/tcp": 13133,  # Health check
        "8888/tcp": 8888,  # OpenTelemetry metrics
        "8889/tcp": 8889,  # Prometheus metrics
    },
    "volumes": {
        "otel-config": {"bind": "/etc/otelcol", "mode": "rw"},
        "otel-data": {"bind": "/var/lib/otelcol", "mode": "rw"},
        "docker-sock": {"bind": "/var/run/docker.sock", "mode": "ro"},
        "app-logs": {"bind": "/var/log/application", "mode": "ro"},
        "infra-logs": {"bind": "/var/log/infrastructure", "mode": "ro"},
    },
    "restart_policy": {"Name": "unless-stopped"},
    "network": "observability-network",
    "resources": {"mem_limit": "512m", "cpus": 0.5},
    "start_timeout": 60,
    "stop_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 5,
    "health_check_interval": 30,
    "health_check_timeout": 10,
    "health_check_retries": 3,
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


def wait_for_healthy_container(container, max_attempts=10):
    """
    Wait for container to be healthy and responsive.
    """
    for attempt in range(max_attempts):
        try:
            container.reload()
            if container.status == "running":
                # Test health endpoint
                health_url = "http://localhost:13133"
                import requests

                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    logging.info("OpenTelemetry Collector is healthy and ready")
                    return True
        except Exception as e:
            logging.debug(f"Health check attempt {attempt + 1} failed: {e}")

        logging.info(
            f"Waiting for container to be ready (attempt {attempt + 1}/{max_attempts})"
        )
        time.sleep(5)

    logging.warning("Container health check failed")
    return False


@activity.defn
async def start_opentelemetry_collector(service_name: str) -> bool:
    """
    Start the OpenTelemetry Collector container with comprehensive telemetry
    configuration.
    """
    logging.info(f"Starting OpenTelemetry Collector for {service_name}")

    required_ports = [4317, 4318, 13133, 8888, 8889]
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
                        logging.info("OpenTelemetry Collector already running")
                        return wait_for_healthy_container(container)
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
                        return wait_for_healthy_container(container)
            except NotFound:
                logging.info("Container not found, creating new one")
                try:
                    client.images.get(CONFIG["image_name"])
                    logging.info("Image already exists, skipping pull")
                except ImageNotFound:
                    logging.info("Pulling OpenTelemetry Collector image")
                    try:
                        client.images.pull(CONFIG["image_name"])
                        logging.info(
                            "OpenTelemetry Collector image pulled successfully"
                        )
                    except Exception as e:
                        logging.exception(
                            f"Failed to pull OpenTelemetry Collector image: {e}"
                        )
                        return False

                try:
                    container = client.containers.run(
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
                        command=[
                            "--config=/etc/otelcol/telemetry.yaml",
                            "--config-dir=/etc/otelcol",
                        ],
                    )
                    logging.info("Container started successfully")

                    # Wait for container to be ready
                    return wait_for_healthy_container(container)

                except Exception as e:
                    logging.exception(f"Failed to create container: {e}")
                    return False

            return True
        except (DockerException, APIError) as e:
            logging.exception(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(CONFIG["retry_delay"])
    logging.error("All attempts to start OpenTelemetry Collector failed")
    return False


@activity.defn
async def stop_opentelemetry_collector(service_name: str) -> bool:
    """
    Stop the OpenTelemetry Collector container.
    """
    logging.info(f"Stopping OpenTelemetry Collector for {service_name}")

    try:
        container = client.containers.get(CONFIG["container_name"])
        container.stop(timeout=CONFIG["stop_timeout"])
        logging.info("OpenTelemetry Collector stopped successfully")
        return True
    except NotFound:
        logging.info("OpenTelemetry Collector container not found")
        return True
    except Exception as e:
        logging.exception(f"Failed to stop OpenTelemetry Collector: {e}")
        return False


@activity.defn
async def get_opentelemetry_collector_status(service_name: str) -> dict:
    """
    Get the status of the OpenTelemetry Collector container.
    """
    logging.info(f"Getting OpenTelemetry Collector status for {service_name}")

    try:
        container = client.containers.get(CONFIG["container_name"])
        container.reload()

        status_info = {
            "container_name": container.name,
            "status": container.status,
            "image": container.image.tags[0] if container.image.tags else "unknown",
            "ports": container.ports,
            "networks": list(container.attrs["NetworkSettings"]["Networks"].keys()),
        }

        logging.info(f"OpenTelemetry Collector status: {status_info}")
        return status_info
    except NotFound:
        logging.info("OpenTelemetry Collector container not found")
        return {"status": "not_found"}
    except Exception as e:
        logging.exception(f"Failed to get OpenTelemetry Collector status: {e}")
        return {"status": "error", "error": str(e)}
