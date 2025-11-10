import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class PromtailManager(BaseService):
    SERVICE_NAME = "Promtail"

    def __init__(self):
        config = ContainerConfig(
            image="grafana/promtail:latest",
            name="promtail-development",
            ports={9080: 9080},
            volumes={
                "promtail-config": "/etc/promtail",
                "/var/log": "/var/log:ro",
                "/var/run/docker.sock": "/var/run/docker.sock:ro"
            },
            network="observability-network",
            memory="128m",
            cpus=0.25,
            restart="unless-stopped",
            environment={},
            extra_params={
                "network_driver": "bridge",
                "start_timeout": 30,
                "stop_timeout": 30,
                "health_check_interval": 30,
                "health_check_timeout": 10,
                "health_check_retries": 3,
            },
        )
        super().__init__(config)


@activity.defn
async def start_promtail_activity(params: Dict[str, Any]) -> bool:
    PromtailManager().run()
    return True


@activity.defn
async def stop_promtail_activity(params: Dict[str, Any]) -> bool:
    PromtailManager().stop(timeout=30)
    return True


@activity.defn
async def restart_promtail_activity(params: Dict[str, Any]) -> bool:
    PromtailManager().restart()
    return True


@activity.defn
async def delete_promtail_activity(params: Dict[str, Any]) -> bool:
    PromtailManager().delete(force=False)
    return True
