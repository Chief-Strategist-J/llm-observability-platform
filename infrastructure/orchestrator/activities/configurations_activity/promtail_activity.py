import logging
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import ContainerConfig, BaseService

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
async def start_promtail_activity(service_name: str) -> bool:
    try:
        manager = PromtailManager()
        manager.run()
        return True
    except Exception as e:
        logger.error("Failed to start Promtail service: %s", e, exc_info=True)
        return False


@activity.defn
async def stop_promtail_activity(service_name: str) -> bool:
    try:
        manager = PromtailManager()
        manager.stop(timeout=30)
        return True
    except Exception as e:
        logger.error("Failed to stop Promtail service: %s", e, exc_info=True)
        return False


@activity.defn
async def restart_promtail_activity(service_name: str) -> bool:
    try:
        manager = PromtailManager()
        manager.restart()
        return True
    except Exception as e:
        logger.error("Failed to restart Promtail service: %s", e, exc_info=True)
        return False


@activity.defn
async def delete_promtail_activity(service_name: str, force: bool = False) -> bool:
    try:
        manager = PromtailManager()
        manager.delete(force=force)
        return True
    except Exception as e:
        logger.error("Failed to delete Promtail service: %s", e, exc_info=True)
        return False
