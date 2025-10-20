#!/usr/bin/env python3
"""Fixed version of your original script: keeps your original structure and settings,
but *does not assume* specific network names. Instead it discovers Loki's Docker
network(s) at runtime and ensures Grafana is attached to at least one of them so
the hostname `loki-development` is resolvable inside the Grafana container.

Save/replace your previous file with this. It preserves your original configs,
behaviour and Temporal activity decorators; only networking/resolution logic was
added and some additional runtime checks.
"""

import logging
import socket
import time

import docker
from docker.errors import APIError, DockerException, ImageNotFound, NotFound
import requests
from temporalio import activity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

GRAFANA_CONFIG = {
    "grafana_url": "http://localhost:31001",
    "admin_user": "admin",
    "admin_password": "SuperSecret123!",
    "loki_url": "http://loki-development:3100",
    "datasource_name": "Loki",
    "dashboard_title": "Logs Pipeline Dashboard",
    "retry_attempts": 5,
    "retry_delay": 3,
}

# Docker client
try:
    client = docker.from_env()
except DockerException as e:
    raise RuntimeError(f"Docker daemon unreachable: {e}")


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def ensure_network(name: str):
    """Create network if it doesn't exist.

    This mirrors your original function but is
    tolerant: if network already exists it returns it, otherwise it creates it.

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


def get_container_networks(container) -> dict:
    """
    Return the Networks dictionary from container.attrs (empty dict if missing).
    """
    try:
        return container.attrs.get("NetworkSettings", {}).get("Networks", {}) or {}
    except Exception:
        return {}


def attach_container_to_network(
    container_name: str, network_name: str, aliases: list = None
):
    """Ensure a container is attached to a network.

    If already attached, do nothing. If not attached, connect it (optionally with
    aliases).

    """
    try:
        net = client.networks.get(network_name)
    except NotFound:
        logger.info("Network %s not found; creating it", network_name)
        net = client.networks.create(network_name)

    try:
        container = client.containers.get(container_name)
    except NotFound:
        raise RuntimeError(
            f"Container {container_name} not found, cannot attach to {network_name}"
        )

    networks = get_container_networks(container)
    if network_name in networks:
        logger.info(
            "Container %s already attached to network %s", container_name, network_name
        )
        return True

    logger.info(
        "Connecting container %s to network %s (aliases=%s)",
        container_name,
        network_name,
        aliases,
    )
    try:
        if aliases:
            net.connect(container, aliases=aliases)
        else:
            net.connect(container)
        logger.info("Connected %s -> %s", container_name, network_name)
        return True
    except APIError as e:
        # If Docker says already connected or another benign error, re-check networks
        logger.exception("Failed to connect container to network: %s", e)
        # re-check
        container.reload()
        networks = get_container_networks(container)
        if network_name in networks:
            logger.info("Connection succeeded after retry (or was already connected).")
            return True
        raise


def ensure_grafana_can_resolve_loki():
    """Check whether the grafana container can resolve 'loki-development' by exec'ing a
    small command.

    Returns True if resolved, False otherwise.

    """
    grafana = get_container(CONTAINER_CONFIG["container_name"])
    if grafana is None:
        logger.error("Grafana container not found when checking DNS resolution")
        return False

    try:
        # Try `getent hosts` first; fallback to ping; fallback to curl
        cmd = 'getent hosts loki-development || ping -c1 -W1 loki-development || curl -sS -o /dev/null -w "%{http_code}" http://loki-development:3100/ready || true'
        exec_result = grafana.exec_run(
            ["/bin/sh", "-c", cmd], stdout=True, stderr=True, demux=False
        )
        output = (
            exec_result.output.decode(errors="ignore") if exec_result.output else ""
        )
        logger.debug("DNS check output: %s", output.strip())

        # simple heuristics: presence of IP (getent) or ping text or HTTP 200
        if (
            "127.0.0.1" in output
            or "172." in output
            or "PING" in output
            or "200" in output
        ):
            logger.info(
                "Grafana container appears to be able to reach loki-development (heuristic match)"
            )
            return True
        logger.info(
            "Grafana could not resolve loki-development (output: %s)", output.strip()
        )
        return False
    except Exception as e:
        logger.exception("Error running DNS check inside grafana container: %s", e)
        return False


@activity.defn
async def start_grafana_container(service_name: str) -> bool:
    logger.info(f"Starting Grafana for {service_name}")

    if is_port_in_use(31001):
        logger.error("Port 31001 already in use")
        return False

    # Make sure the declared network exists (this mirrors your previous ensure_network)
    try:
        ensure_network(CONTAINER_CONFIG["network"])
    except Exception as e:
        logger.exception("Failed to ensure network: %s", e)
        # continue: we try to start container anyway; network attach logic later will handle it

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

                # Create the container using the same config you had (no semantic changes)
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


def wait_for_grafana_ready():
    """
    Wait for Grafana to be ready (host-mapped endpoint).
    """
    for attempt in range(GRAFANA_CONFIG["retry_attempts"]):
        try:
            response = requests.get(
                f"{GRAFANA_CONFIG['grafana_url']}/api/health", timeout=5
            )
            if response.status_code == 200:
                logger.info("Grafana is ready")
                return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}: Grafana not ready yet: {e}")
            time.sleep(GRAFANA_CONFIG["retry_delay"])
    return False


def configure_loki_datasource():
    """
    Configure Loki as a datasource in Grafana (host endpoint).
    """
    datasource_payload = {
        "name": GRAFANA_CONFIG["datasource_name"],
        "type": "loki",
        "url": GRAFANA_CONFIG["loki_url"],
        "access": "proxy",
        "isDefault": True,
        "jsonData": {},
    }

    try:
        response = requests.post(
            f"{GRAFANA_CONFIG['grafana_url']}/api/datasources",
            json=datasource_payload,
            auth=(GRAFANA_CONFIG["admin_user"], GRAFANA_CONFIG["admin_password"]),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 200:
            logger.info(f"Loki datasource created successfully: {response.json()}")
            return True
        if response.status_code == 409:
            logger.info("Loki datasource already exists")
            return True
        logger.error(
            f"Failed to create datasource: {response.status_code} - {response.text}"
        )
        return False
    except requests.exceptions.RequestException as e:
        logger.exception(f"Error configuring Loki datasource: {e}")
        return False


def create_logs_dashboard():
    """
    Create a logs dashboard in Grafana (kept as in original).
    """
    dashboard_payload = {
        "dashboard": {
            "title": GRAFANA_CONFIG["dashboard_title"],
            "tags": ["logs", "loki"],
            "timezone": "browser",
            "schemaVersion": 16,
            "version": 0,
            "refresh": "5s",
            "panels": [
                {
                    "id": 1,
                    "title": "Log Volume",
                    "type": "graph",
                    "datasource": GRAFANA_CONFIG["datasource_name"],
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 0},
                    "targets": [
                        {
                            "expr": 'sum(rate({job=~".+"}[1m]))',
                            "refId": "A",
                        }
                    ],
                },
                {
                    "id": 2,
                    "title": "Recent Logs",
                    "type": "logs",
                    "datasource": GRAFANA_CONFIG["datasource_name"],
                    "gridPos": {"h": 16, "w": 24, "x": 0, "y": 8},
                    "targets": [
                        {
                            "expr": '{job=~".+"}',
                            "refId": "A",
                        }
                    ],
                    "options": {
                        "showTime": True,
                        "showLabels": True,
                        "wrapLogMessage": True,
                    },
                },
            ],
        },
        "overwrite": True,
    }

    try:
        response = requests.post(
            f"{GRAFANA_CONFIG['grafana_url']}/api/dashboards/db",
            json=dashboard_payload,
            auth=(GRAFANA_CONFIG["admin_user"], GRAFANA_CONFIG["admin_password"]),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Dashboard created successfully: {result.get('url')}")
            return True
        logger.error(
            f"Failed to create dashboard: {response.status_code} - {response.text}"
        )
        return False
    except requests.exceptions.RequestException as e:
        logger.exception(f"Error creating dashboard: {e}")
        return False


def ensure_networking_for_loki_resolution():
    """Core fix: ensure Grafana can resolve `loki-development`.
    Strategy (non-assumptive):
      1. If a container named 'loki-development' exists, get its networks.
      2. Attempt to connect the Grafana container to at least one of Loki's networks
         (so Docker internal DNS will resolve the hostname).
      3. If Grafana already resolves Loki, do nothing.
      4. If Loki container not found, log and return False (we don't create Loki here to avoid assumptions).
    """
    loki = get_container("loki-development")
    grafana = get_container(CONTAINER_CONFIG["container_name"])

    if grafana is None:
        logger.error(
            "Grafana container '%s' not found; cannot ensure networking",
            CONTAINER_CONFIG["container_name"],
        )
        return False

    # If grafana already resolves loki, we're done.
    if ensure_grafana_can_resolve_loki():
        logger.info(
            "Grafana already resolves loki-development; no networking changes required"
        )
        return True

    if loki is None:
        logger.error(
            "Loki container 'loki-development' not found. Networking cannot be fixed automatically."
        )
        # Do not create Loki automatically (no assumptions) — return False so caller can handle.
        return False

    # Loki exists: enumerate Loki's networks and try to attach Grafana to them (one by one)
    loki_networks = get_container_networks(loki)
    if not loki_networks:
        logger.error("Loki container has no network attachments (unexpected).")
        return False

    # try each network until Grafana can resolve loki
    for net_name in loki_networks.keys():
        try:
            logger.info("Attempting to attach Grafana to Loki's network: %s", net_name)
            attach_container_to_network(
                CONTAINER_CONFIG["container_name"],
                net_name,
                aliases=["loki-development"],
            )
            # Small wait to let Docker DNS update
            time.sleep(1.0)
            # reload grafana container attrs and test resolution
            grafana.reload()
            if ensure_grafana_can_resolve_loki():
                logger.info(
                    "Grafana can now resolve loki-development via network %s", net_name
                )
                return True
            logger.warning(
                "After attaching to %s, grafana still cannot resolve loki-development",
                net_name,
            )
        except Exception as e:
            logger.exception("Failed to attach Grafana to network %s: %s", net_name, e)

    logger.error(
        "Tried all Loki networks but Grafana still cannot resolve loki-development"
    )
    return False


@activity.defn
async def configure_grafana(service_name: str) -> bool:
    """Configure Grafana with Loki datasource and logs dashboard.

    This wraps your original flow but first ensures networking so Grafana can resolve
    `loki-development` from inside the container.

    """
    logger.info(f"Configuring Grafana for {service_name}")

    if not wait_for_grafana_ready():
        logger.error("Grafana failed to become ready")
        return False

    # --- NEW: ensure grafana can resolve loki (attach networks as needed) ---
    # If this fails, we log an error and abort configuration (so user can decide next steps)
    try:
        ok = ensure_networking_for_loki_resolution()
        if not ok:
            logger.error(
                "Networking check failed: Grafana cannot resolve loki-development. Aborting configuration."
            )
            return False
    except Exception as e:
        logger.exception("Unexpected error while ensuring networking for Loki: %s", e)
        return False

    # --- original steps ---
    if not configure_loki_datasource():
        logger.error("Failed to configure Loki datasource")
        return False

    if not create_logs_dashboard():
        logger.error("Failed to create logs dashboard")
        return False

    logger.info("Grafana configuration completed successfully")
    return True


# If you want to run the script directly (not via Temporal), here's a helper main()
if __name__ == "__main__":
    # This main() reproduces the original higher-level flow:
    svc = "local-service"
    # Try to ensure Grafana is started (same as your activity)
    started = None
    try:
        # If Grafana container is missing, start it (reuse your function)
        started = None
        grafana_container = get_container(CONTAINER_CONFIG["container_name"])
        if grafana_container is None:
            logger.info("Grafana container not present; attempting to start it.")
            # call start_grafana_container synchronously through its logic: it is async in your code,
            # but for direct invocation use a blocking wrapper by calling its inner logic via Docker SDK directly.
            # To avoid duplicating start logic, just call start_grafana_container in a simple event loop.
            import asyncio

            started = asyncio.get_event_loop().run_until_complete(
                start_grafana_container(svc)
            )
        else:
            logger.info(
                "Grafana container already present (status=%s)",
                grafana_container.status,
            )
            started = True

        if not started:
            logger.error("Failed to ensure Grafana is running; exiting.")
            raise SystemExit(1)

        # Wait for Grafana to be ready on the host port
        if not wait_for_grafana_ready():
            logger.error("Grafana didn't become ready on host port; exiting.")
            raise SystemExit(1)

        # Ensure networking so grafana can resolve loki
        if not ensure_networking_for_loki_resolution():
            logger.error(
                "Networking check failed. Please ensure a Loki container named 'loki-development' exists or attach networks manually."
            )
            raise SystemExit(1)

        # Configure Grafana
        if not configure_loki_datasource():
            logger.error("Datasource configuration failed")
            raise SystemExit(1)

        if not create_logs_dashboard():
            logger.error("Dashboard creation failed")
            raise SystemExit(1)

        logger.info("All steps completed successfully.")
    except Exception as exc:
        logger.exception("Unhandled error in script: %s", exc)
        raise
