import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class PromtailManager(BaseService):
    SERVICE_NAME = "Promtail"

    def __init__(self, instance_id: int = 0):
        pm = get_port_manager()

        port = pm.get_port("promtail", instance_id, "port")

        config = ContainerConfig(
            image="grafana/promtail:latest",
            name=f"promtail-instance-{instance_id}",
            ports={port: port},
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
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    f"wget --no-verbose --tries=1 --spider http://localhost:{port}/ready || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 20000000000
            }
        )

        logger.info(
            "event=promtail_manager_init service=promtail instance=%s port=%s",
            instance_id, port
        )

        super().__init__(config)


@activity.defn
async def start_promtail_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=promtail_start params=%s", params)
    PromtailManager().run()
    logger.info("event=promtail_started")
    return True


@activity.defn
async def stop_promtail_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=promtail_stop_begin")
    PromtailManager().stop(timeout=30)
    logger.info("event=promtail_stop_complete")
    return True


@activity.defn
async def restart_promtail_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=promtail_restart_begin")
    PromtailManager().restart()
    logger.info("event=promtail_restart_complete")
    return True


@activity.defn
async def delete_promtail_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=promtail_delete_begin")
    PromtailManager().delete(force=False)
    logger.info("event=promtail_delete_complete")
    return True
