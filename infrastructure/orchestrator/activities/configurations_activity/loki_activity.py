import logging
from typing import Optional
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import (
    BaseService,
    ContainerConfig,
)

logger = logging.getLogger(__name__)


class LokiManager(BaseService):
    SERVICE_NAME = "Loki"
    SERVICE_DESCRIPTION = "log aggregation service"
    DEFAULT_PORT = 31002
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, config: Optional[ContainerConfig] = None) -> None:
        if config is None:
            config = ContainerConfig(
                image="grafana/loki:latest",
                name="loki-development",
                ports={3100: 31002},
                volumes={"loki-data": "/loki"},
                network="monitoring-bridge",
                memory="256m",
                memory_reservation="128m",
                cpus=0.5,
                restart="unless-stopped",
                environment={"LOKI_CONFIG_USE_INGRESS": "true"},
                healthcheck={
                    "test": [
                        "CMD-SHELL",
                        "wget --no-verbose --tries=1 --spider "
                        "http://localhost:3100/ready || exit 1",
                    ],
                    "interval": 30000000000,
                    "timeout": 10000000000,
                    "retries": 3,
                    "start_period": 40000000000,
                },
            )
        extra_data = {"ingress_enabled": "true"}
        super().__init__(config=config, extra=extra_data)
        logger.info("LokiManager initialized")

    def query_logs(self, query: str, limit: int = 100) -> str:
        cmd = (
            f'wget -qO- "http://localhost:3100/loki/api/v1/query'
            f'?query={query}&limit={limit}"'
        )
        code, out = self.exec(cmd)
        if code != 0:
            logger.error("Failed to query logs: %s", out)
            return ""
        return out

    def get_labels(self) -> str:
        cmd = 'wget -qO- "http://localhost:3100/loki/api/v1/labels"'
        code, out = self.exec(cmd)
        if code != 0:
            logger.error("Failed to get labels: %s", out)
            return ""
        return out


@activity.defn
async def start_loki_activity(service_name: str) -> bool:
    try:
        loki = LokiManager()
        loki.run()
        return True
    except Exception as e:
        msg = f"Failed to start Loki service {service_name}: {e}"
        logger.error(msg, exc_info=True)
        raise activity.ActivityError(msg) from e


@activity.defn
async def stop_loki_activity(service_name: str) -> bool:
    try:
        loki = LokiManager()
        loki.stop(timeout=30)
        return True
    except Exception as e:
        msg = f"Failed to stop Loki service {service_name}: {e}"
        logger.error(msg, exc_info=True)
        raise activity.ActivityError(msg) from e


@activity.defn
async def restart_loki_activity(service_name: str) -> bool:
    try:
        loki = LokiManager()
        loki.restart()
        return True
    except Exception as e:
        msg = f"Failed to restart Loki service {service_name}: {e}"
        logger.error(msg, exc_info=True)
        raise activity.ActivityError(msg) from e


@activity.defn
async def delete_loki_activity(
    service_name: str, force: bool = False
) -> bool:
    try:
        loki = LokiManager()
        loki.delete(force=force)
        return True
    except Exception as e:
        msg = f"Failed to delete Loki service {service_name}: {e}"
        logger.error(msg, exc_info=True)
        raise activity.ActivityError(msg) from e
