import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class TraefikManager(BaseService):
    SERVICE_NAME = "Traefik"
    SERVICE_DESCRIPTION = "reverse proxy and edge router"
    DEFAULT_PORT = 80
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self):
        config = ContainerConfig(
            image="traefik:v3.5",
            name="traefik-development",
            ports={
                80: 80,           # HTTP entry point
                8888: 8888,       # Dashboard (changed from 8080 - Temporal uses that)
                31001: 31001,     # Grafana proxy
                31002: 31002,     # Loki proxy
                31003: 31003,     # OTel proxy
            },
            volumes={
                "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "ro"},
            },
            network="observability-network",
            memory="256m",
            memory_reservation="128m",
            cpus=0.5,
            restart="unless-stopped",
            command=[
                "--providers.docker=true",
                "--providers.docker.exposedByDefault=false",
                "--providers.docker.endpoint=unix:///var/run/docker.sock",
                "--providers.docker.network=observability-network",
                "--api.dashboard=true",
                "--api.insecure=true",
                "--entrypoints.web.address=:80",
                "--entrypoints.grafana.address=:31001",
                "--entrypoints.loki.address=:31002",
                "--entrypoints.otel.address=:31003",
                "--log.level=INFO",
                "--ping=true",
            ],
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "wget --no-verbose --tries=1 --spider http://localhost:8888/ping || exit 1"
                ],
                "interval": 30_000_000_000,
                "timeout": 10_000_000_000,
                "retries": 3,
                "start_period": 20_000_000_000
            },
        )
        super().__init__(config)

    def get_dashboard_status(self) -> str:
        try:
            cmd = 'wget -qO- "http://localhost:8888/api/rawdata"'
            code, output = self.exec(cmd)
            if code != 0:
                logger.error("Dashboard status query failed: %s", output)
                return ""
            return output
        except Exception as e:
            logger.exception("Error fetching dashboard status: %s", e)
            return ""


@activity.defn
async def start_traefik_activity(params: Dict[str, Any]) -> bool:
    logger.info("Activity: start_traefik_activity called")
    try:
        manager = TraefikManager()
        
        # Check if container already exists
        existing = manager.manager._get_existing_container()
        if existing:
            logger.info("Traefik container already exists")
            # Check if it's running
            existing.reload()
            if existing.status == "running":
                logger.info("Traefik already running")
                return True
            else:
                logger.info("Starting existing Traefik container")
                try:
                    existing.start()
                    logger.info("Traefik started successfully")
                    return True
                except Exception as e:
                    logger.warning("Failed to start existing container, will recreate: %s", e)
                    # Remove the failed container
                    try:
                        existing.remove(force=True)
                    except Exception:
                        pass
        
        # Start new container
        manager.run()
        logger.info("Traefik started successfully")
        return True
    except Exception as e:
        logger.exception("Failed to start Traefik: %s", e)
        return False


@activity.defn
async def stop_traefik_activity(params: Dict[str, Any]) -> bool:
    logger.info("Activity: stop_traefik_activity called")
    try:
        manager = TraefikManager()
        manager.stop(timeout=30)
        return True
    except Exception as e:
        logger.exception("Failed to stop Traefik: %s", e)
        return False


@activity.defn
async def restart_traefik_activity(params: Dict[str, Any]) -> bool:
    logger.info("Activity: restart_traefik_activity called")
    try:
        manager = TraefikManager()
        manager.restart()
        return True
    except Exception as e:
        logger.exception("Failed to restart Traefik: %s", e)
        return False


@activity.defn
async def delete_traefik_activity(params: Dict[str, Any]) -> bool:
    logger.info("Activity: delete_traefik_activity called")
    try:
        manager = TraefikManager()
        manager.delete(force=False)
        return True
    except Exception as e:
        logger.exception("Failed to delete Traefik: %s", e)
        return False