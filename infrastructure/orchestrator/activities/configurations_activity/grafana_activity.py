import logging
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class GrafanaManager(BaseService):
    SERVICE_NAME = "Grafana"
    SERVICE_DESCRIPTION = "monitoring and visualization dashboard"
    DEFAULT_PORT = 31001
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self):
        config = ContainerConfig(
            image="grafana/grafana:latest",
            name="grafana-development",
            ports={3000: 31001},
            volumes={"grafana-data": "/var/lib/grafana"},
            network="monitoring-bridge",
            memory="256m",
            memory_reservation="128m",
            cpus=0.5,
            restart="unless-stopped",
            environment={
                "GF_SECURITY_ADMIN_USER": "admin",
                "GF_SECURITY_ADMIN_PASSWORD": "SuperSecret123!",
                "GF_USERS_ALLOW_SIGN_UP": "false",
            },
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )
        super().__init__(config)

    def create_datasource(self, name: str, url: str, ds_type: str = "prometheus") -> str:
        command = (
            f'curl -X POST http://localhost:3000/api/datasources '
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
async def start_grafana_activity(service_name: str) -> bool:
    try:
        manager = GrafanaManager()
        manager.run()
        return True
    except Exception as e:
        logger.error("Failed to start Grafana service: %s", e, exc_info=True)
        return False


@activity.defn
async def stop_grafana_activity(service_name: str) -> bool:
    try:
        manager = GrafanaManager()
        manager.stop(timeout=30)
        return True
    except Exception as e:
        logger.error("Failed to stop Grafana service: %s", e, exc_info=True)
        return False


@activity.defn
async def restart_grafana_activity(service_name: str) -> bool:
    try:
        manager = GrafanaManager()
        manager.restart()
        return True
    except Exception as e:
        logger.error("Failed to restart Grafana service: %s", e, exc_info=True)
        return False


@activity.defn
async def delete_grafana_activity(service_name: str, force: bool = False) -> bool:
    try:
        manager = GrafanaManager()
        manager.delete(force=force)
        return True
    except Exception as e:
        logger.error("Failed to delete Grafana service: %s", e, exc_info=True)
        return False
