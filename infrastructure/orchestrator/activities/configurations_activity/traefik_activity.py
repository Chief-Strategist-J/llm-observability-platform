import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class TraefikManager(BaseService):
    SERVICE_NAME = "Traefik"
    SERVICE_DESCRIPTION = "reverse proxy and edge router"
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0):
        pm = get_port_manager()

        http_port = pm.get_port("traefik", instance_id, "http_port")
        grafana_port = pm.get_port("traefik", instance_id, "grafana_entrypoint")
        loki_port = pm.get_port("traefik", instance_id, "loki_entrypoint")
        otel_port = pm.get_port("traefik", instance_id, "otel_entrypoint")

        ports = {
            http_port: http_port,
            grafana_port: grafana_port,
            loki_port: loki_port,
            otel_port: otel_port
        }

        config = ContainerConfig(
            image="traefik:v3.5",
            name=f"traefik-instance-{instance_id}",
            ports=ports,
            volumes={
                "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "ro"}
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
                f"--entrypoints.web.address=:{http_port}",
                f"--entrypoints.grafana.address=:{grafana_port}",
                f"--entrypoints.loki.address=:{loki_port}",
                f"--entrypoints.otel.address=:{otel_port}",
                "--log.level=INFO"
            ],
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    f"wget --no-verbose --tries=1 --spider http://localhost:{http_port}/api/overview || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 20000000000
            }
        )

        logger.info(
            "event=traefik_manager_init service=traefik instance=%s web=%s grafana=%s loki=%s otel=%s",
            instance_id, http_port, grafana_port, loki_port, otel_port
        )

        super().__init__(config)

    def get_dashboard_status(self) -> str:
        http_port = list(self.config.ports.keys())[0]
        cmd = f'wget -qO- "http://localhost:{http_port}/api/rawdata"'
        code, out = self.exec(cmd)

        if code != 0:
            logger.error("event=traefik_dashboard_query_failed output=%s", out)
            return ""

        logger.info("event=traefik_dashboard_query_success")
        return out


@activity.defn
async def start_traefik_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=traefik_start params=%s", params)
    manager = TraefikManager()

    try:
        existing = manager.manager._get_existing_container()
        if existing:
            existing.reload()
            if existing.status == "running":
                logger.info("event=traefik_already_running")
                return True

            logger.info("event=traefik_starting_existing")
            try:
                existing.start()
                logger.info("event=traefik_started_existing")
                return True
            except Exception as e:
                logger.warning("event=traefik_restart_existing_failed error=%s", e)
                try:
                    existing.remove(force=True)
                except Exception:
                    pass

        manager.run()
        logger.info("event=traefik_started_new")
        return True

    except Exception as e:
        logger.exception("event=traefik_start_failed error=%s", e)
        return False


@activity.defn
async def stop_traefik_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=traefik_stop_begin")
    try:
        TraefikManager().stop(timeout=30)
        logger.info("event=traefik_stopped")
        return True
    except Exception as e:
        logger.exception("event=traefik_stop_failed error=%s", e)
        return False


@activity.defn
async def restart_traefik_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=traefik_restart_begin")
    try:
        TraefikManager().restart()
        logger.info("event=traefik_restart_complete")
        return True
    except Exception as e:
        logger.exception("event=traefik_restart_failed error=%s", e)
        return False


@activity.defn
async def delete_traefik_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=traefik_delete_begin")
    try:
        TraefikManager().delete(force=False)
        logger.info("event=traefik_delete_complete")
        return True
    except Exception as e:
        logger.exception("event=traefik_delete_failed error=%s", e)
        return False
