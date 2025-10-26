import logging
import socket
import time

import docker
from docker.errors import APIError, DockerException, ImageNotFound, NotFound
from temporalio import activity

# Service Access Information:
# Redis Server: redis://localhost:6379
# Redis CLI: redis-cli -h localhost -p 6379
# Redis Insight: http://localhost:8001 (if using redisinsight image)
# Username: N/A (No authentication by default)
# Password: N/A
# Purpose: In-memory data store, caching, session management, pub/sub messaging

logging.basicConfig(level=logging.INFO)

CONFIG = {
    "image_name": "redis:7-alpine",
    "container_name": "redis-development",
    "environment": {
        "REDIS_PASSWORD": "",  # Empty for development, set for production
        "REDIS_DATABASES": "16",
        "REDIS_MAXMEMORY": "256mb",
        "REDIS_MAXMEMORY_POLICY": "allkeys-lru",
    },
    "ports": {
        "6379/tcp": 6379,  # Redis server port
    },
    "volumes": {
        "redis-data": {"bind": "/data", "mode": "rw"},
        "redis-config": {"bind": "/usr/local/etc/redis", "mode": "rw"},
    },
    "restart_policy": {"Name": "unless-stopped"},
    "network": "observability-network",
    "resources": {"mem_limit": "256m", "cpus": 0.5},
    "start_timeout": 30,
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


def wait_for_redis_ready(container, max_attempts=10):
    """Wait for Redis to be ready to accept connections"""
    import redis

    for attempt in range(max_attempts):
        try:
            container.reload()
            if container.status == "running":
                # Test Redis connection
                try:
                    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
                    r.ping()
                    logging.info("Redis is ready to accept connections")
                    return True
                except redis.ConnectionError:
                    logging.debug(f"Redis connection attempt {attempt + 1} failed")
        except Exception as e:
            logging.debug(f"Readiness check attempt {attempt + 1} failed: {e}")

        logging.info(f"Waiting for Redis to be ready (attempt {attempt + 1}/{max_attempts})")
        time.sleep(3)

    logging.warning("Redis readiness check failed")
    return False


@activity.defn
async def start_redis_container(service_name: str) -> bool:
    """Start Redis for caching and data storage"""
    logging.info(f"Starting Redis for {service_name}")

    if is_port_in_use(6379):
        logging.error("Port 6379 already in use")
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
                        logging.info("Redis already running")
                        return wait_for_redis_ready(container)
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
                        return wait_for_redis_ready(container)
            except NotFound:
                logging.info("Container not found, creating new one")
                try:
                    client.images.get(CONFIG["image_name"])
                    logging.info("Image already exists, skipping pull")
                except ImageNotFound:
                    logging.info("Pulling Redis image")
                    try:
                        client.images.pull(CONFIG["image_name"])
                        logging.info("Redis image pulled successfully")
                    except Exception as e:
                        logging.exception(f"Failed to pull Redis image: {e}")
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
                            "redis-server",
                            "--appendonly", "yes",
                            "--maxmemory", CONFIG["environment"]["REDIS_MAXMEMORY"],
                            "--maxmemory-policy", CONFIG["environment"]["REDIS_MAXMEMORY_POLICY"],
                            "--databases", CONFIG["environment"]["REDIS_DATABASES"],
                        ],
                    )
                    logging.info("Redis container started successfully")

                    return wait_for_redis_ready(container)

                except Exception as e:
                    logging.exception(f"Failed to create Redis container: {e}")
                    return False

            return True
        except (DockerException, APIError) as e:
            logging.exception(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(CONFIG["retry_delay"])
    logging.error("All attempts to start Redis failed")
    return False


@activity.defn
async def stop_redis_container(service_name: str) -> bool:
    """Stop Redis container"""
    logging.info(f"Stopping Redis for {service_name}")

    try:
        container = client.containers.get(CONFIG["container_name"])
        container.stop(timeout=CONFIG["stop_timeout"])
        logging.info("Redis stopped successfully")
        return True
    except NotFound:
        logging.info("Redis container not found")
        return True
    except Exception as e:
        logging.exception(f"Failed to stop Redis: {e}")
        return False


@activity.defn
async def get_redis_status(service_name: str) -> dict:
    """Get Redis container status and connection information"""
    logging.info(f"Getting Redis status for {service_name}")

    try:
        container = client.containers.get(CONFIG["container_name"])
        container.reload()

        status_info = {
            "container_name": container.name,
            "status": container.status,
            "image": container.image.tags[0] if container.image.tags else "unknown",
            "ports": container.ports,
            "connection_url": "redis://localhost:6379",
            "networks": list(container.attrs["NetworkSettings"]["Networks"].keys()),
        }

        logging.info(f"Redis status: {status_info}")
        return status_info
    except NotFound:
        logging.info("Redis container not found")
        return {"status": "not_found"}
    except Exception as e:
        logging.exception(f"Failed to get Redis status: {e}")
        return {"status": "error", "error": str(e)}
