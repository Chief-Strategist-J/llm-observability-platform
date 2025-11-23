import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class GrafanaManager(BaseService):
    SERVICE_NAME = "Grafana"
    SERVICE_DESCRIPTION = "monitoring and visualization dashboard"
    DEFAULT_PORT = 3000
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self):
        config = ContainerConfig(
            image="grafana/grafana:latest",
            name="grafana-development",
            ports={},  # No direct ports; access through Traefik only
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
                "GF_SERVER_ROOT_URL": "http://localhost:31001",
            },
            labels={
                # Enable Traefik for this container
                "traefik.enable": "true",
                
                # HTTP router for Grafana
                "traefik.http.routers.grafana.rule": "PathPrefix(`/`)",
                "traefik.http.routers.grafana.entrypoints": "grafana",
                "traefik.http.routers.grafana.service": "grafana",
                
                # Service configuration
                "traefik.http.services.grafana.loadbalancer.server.port": "3000",
                
                # Network
                "traefik.docker.network": "observability-network",
            },
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1"
                ],
                "interval": 30_000_000_000,
                "timeout": 10_000_000_000,
                "retries": 3,
                "start_period": 20_000_000_000
            }
        )
        super().__init__(config)

    def create_datasource(self, name: str, url: str, ds_type: str = "loki") -> str:
        # Use internal container name for datasource URL (containers talk directly)
        command = (
            f'curl -s -X POST http://localhost:3000/api/datasources '
            f'-H "Content-Type: application/json" '
            f'-u admin:SuperSecret123! '
            f"-d '{{\"name\":\"{name}\",\"type\":\"{ds_type}\",\"url\":\"{url}\",\"access\":\"proxy\"}}'"
        )
        exit_code, output = self.exec(command)
        if exit_code != 0:
            logger.error("Failed to create datasource: %s", output)
            return ""
        return output


@activity.defn
async def start_grafana_activity(params: Dict[str, Any]) -> bool:
    manager = GrafanaManager()
    manager.run()
    return True


@activity.defn
async def stop_grafana_activity(params: Dict[str, Any]) -> bool:
    manager = GrafanaManager()
    manager.stop(timeout=30)
    return True


@activity.defn
async def restart_grafana_activity(params: Dict[str, Any]) -> bool:
    manager = GrafanaManager()
    manager.restart()
    return True


@activity.defn
async def delete_grafana_activity(params: Dict[str, Any]) -> bool:
    manager = GrafanaManager()
    manager.delete(force=False)
    return True