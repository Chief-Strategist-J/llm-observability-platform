#!/usr/bin/env python3
"""Grafana configure activity - handles configuring Grafana with Loki datasource and dashboard."""

import logging
import time

import docker
from docker.errors import NotFound
import requests
from temporalio import activity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Docker client
try:
    client = docker.from_env()
except Exception as e:
    raise RuntimeError(f"Docker daemon unreachable: {e}")


def get_container(name: str):
    """
    Get container by name.
    """
    try:
        return client.containers.get(name)
    except NotFound:
        return None


def get_container_networks(container) -> dict:
    """
    Return the Networks dictionary from container.attrs.
    """
    try:
        return container.attrs.get("NetworkSettings", {}).get("Networks", {}) or {}
    except Exception:
        return {}


def attach_container_to_network(
    container_name: str, network_name: str, aliases: list = None
):
    """
    Ensure a container is attached to a network.
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
    except Exception as e:
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
    """
    Check whether the grafana container can resolve 'loki-development'.
    """
    grafana = get_container("grafana-development")
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


def wait_for_grafana_ready():
    """
    Wait for Grafana to be ready.
    """
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
    Configure Loki as a datasource in Grafana.
    """
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
    Create a logs dashboard in Grafana.
    """
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
    """Core fix: ensure Grafana can resolve `loki-development`."""
    loki = get_container("loki-development")
    grafana = get_container("grafana-development")

    if grafana is None:
        logger.error(
            "Grafana container 'grafana-development' not found; cannot ensure networking"
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
        return False

    # Loki exists: enumerate Loki's networks and try to attach Grafana to them
    loki_networks = get_container_networks(loki)
    if not loki_networks:
        logger.error("Loki container has no network attachments (unexpected).")
        return False

    # try each network until Grafana can resolve loki
    for net_name in loki_networks.keys():
        try:
            logger.info("Attempting to attach Grafana to Loki's network: %s", net_name)
            attach_container_to_network(
                "grafana-development",
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
    """
    Configure Grafana with Loki datasource and logs dashboard.
    """
    logger.info(f"Configuring Grafana for {service_name}")

    if not wait_for_grafana_ready():
        logger.error("Grafana failed to become ready")
        return False

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

    if not configure_loki_datasource():
        logger.error("Failed to configure Loki datasource")
        return False

    if not create_logs_dashboard():
        logger.error("Failed to create logs dashboard")
        return False

    logger.info("Grafana configuration completed successfully")
    return True
