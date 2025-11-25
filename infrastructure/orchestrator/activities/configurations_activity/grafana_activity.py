import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class GrafanaManager(BaseService):
    SERVICE_NAME = "Grafana"
    SERVICE_DESCRIPTION = "monitoring and visualization dashboard"
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0):
        pm = get_port_manager()
        host_port = pm.get_port("grafana", instance_id, "port")

        config = ContainerConfig(
            image="grafana/grafana:latest",
            name=f"grafana-instance-{instance_id}",
            ports={host_port: host_port},
            volumes={"grafana-data": {"bind": "/var/lib/grafana", "mode": "rw"}},
            network="observability-network",
            memory="512m",
            memory_reservation="256m",
            cpus=0.5,
            restart="unless-stopped",
            environment={
                "GF_SECURITY_ADMIN_USER": "admin",
                "GF_SECURITY_ADMIN_PASSWORD": "SuperSecret123!",
                "GF_USERS_ALLOW_SIGN_UP": "false",
                "GF_SERVER_HTTP_PORT": "3000",
                "GF_SERVER_ROOT_URL": f"http://localhost:{host_port}"
            },
            labels={
                "traefik.enable": "true",
                "traefik.http.routers.grafana.rule": "PathPrefix(`/`)",
                "traefik.http.routers.grafana.entrypoints": "grafana",
                "traefik.http.routers.grafana.service": "grafana",
                "traefik.http.services.grafana.loadbalancer.server.port": "3000",
                "traefik.docker.network": "observability-network"
            },
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    f"wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 20000000000
            }
        )

        logger.info(
            "event=grafana_manager_init service=grafana instance=%s host_port=%s",
            instance_id, host_port
        )

        super().__init__(config)

    def create_datasource(self, name: str, url: str, ds_type: str = "loki") -> str:
        command = (
            f'curl -s -X POST http://localhost:3000/api/datasources '
            f'-H "Content-Type: application/json" '
            f'-u admin:SuperSecret123! '
            f"-d '{{\"name\":\"{name}\",\"type\":\"{ds_type}\",\"url\":\"{url}\",\"access\":\"proxy\"}}'"
        )

        exit_code, output = self.exec(command)

        if exit_code != 0:
            logger.error(
                "event=grafana_datasource_create_failed name=%s url=%s output=%s",
                name, url, output
            )
            return ""

        logger.info(
            "event=grafana_datasource_created name=%s url=%s",
            name, url
        )

        return output


@activity.defn
async def start_grafana_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=grafana_start params=%s", params)
    manager = GrafanaManager()
    manager.run()
    logger.info("event=grafana_started")
    return True


@activity.defn
async def stop_grafana_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=grafana_stop_begin")
    manager = GrafanaManager()
    manager.stop(timeout=30)
    logger.info("event=grafana_stop_complete")
    return True


@activity.defn
async def restart_grafana_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=grafana_restart_begin")
    manager = GrafanaManager()
    manager.restart()
    logger.info("event=grafana_restart_complete")
    return True


@activity.defn
async def delete_grafana_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=grafana_delete_begin")
    manager = GrafanaManager()
    manager.delete(force=False)
    logger.info("event=grafana_delete_complete")
    return True
