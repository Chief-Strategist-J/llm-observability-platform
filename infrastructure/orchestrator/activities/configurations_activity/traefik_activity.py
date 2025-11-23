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
                80: 80,
                31001: 31001,
                31002: 31002,
                31003: 31003,
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
            ],
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "traefik healthcheck --ping || exit 1"
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
            cmd = 'wget -qO- "http://localhost:80/api/rawdata"'
            code, output = self.exec(cmd)
            if code != 0:
                logger.error("traefik_dashboard_query_failed output=%s", output)
                return ""
            return output
        except Exception as e:
            logger.exception("traefik_dashboard_error error=%s", e)
            return ""


@activity.defn
async def start_traefik_activity(params: Dict[str, Any]) -> bool:
    logger.info("traefik_start_activity_called params=%s", list(params.keys()))
    try:
        manager = TraefikManager()
        
        existing = manager.manager._get_existing_container()
        if existing:
            logger.info("traefik_container_exists status=%s", existing.status)
            existing.reload()
            if existing.status == "running":
                logger.info("traefik_already_running")
                return True
            else:
                logger.info("traefik_starting_existing")
                try:
                    existing.start()
                    logger.info("traefik_started_successfully")
                    return True
                except Exception as e:
                    logger.warning("traefik_start_failed_recreating error=%s", e)
                    try:
                        existing.remove(force=True)
                    except Exception:
                        pass
        
        manager.run()
        logger.info("traefik_created_and_started")
        return True
    except Exception as e:
        logger.exception("traefik_start_failed error=%s", e)
        return False


@activity.defn
async def stop_traefik_activity(params: Dict[str, Any]) -> bool:
    logger.info("traefik_stop_activity_called")
    try:
        manager = TraefikManager()
        manager.stop(timeout=30)
        logger.info("traefik_stopped")
        return True
    except Exception as e:
        logger.exception("traefik_stop_failed error=%s", e)
        return False


@activity.defn
async def restart_traefik_activity(params: Dict[str, Any]) -> bool:
    logger.info("traefik_restart_activity_called")
    try:
        manager = TraefikManager()
        manager.restart()
        logger.info("traefik_restarted")
        return True
    except Exception as e:
        logger.exception("traefik_restart_failed error=%s", e)
        return False


@activity.defn
async def delete_traefik_activity(params: Dict[str, Any]) -> bool:
    logger.info("traefik_delete_activity_called")
    try:
        manager = TraefikManager()
        manager.delete(force=False)
        logger.info("traefik_deleted")
        return True
    except Exception as e:
        logger.exception("traefik_delete_failed error=%s", e)
        return False