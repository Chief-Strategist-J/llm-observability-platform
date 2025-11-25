import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)

class AlertmanagerManager(BaseService):
    SERVICE_NAME = "Alertmanager"
    SERVICE_DESCRIPTION = "alert routing and management"
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0):
        pm = get_port_manager()
        alertmanager_port = pm.get_port("alertmanager", instance_id, "port")

        config = ContainerConfig(
            image="prom/alertmanager:latest",
            name=f"alertmanager-instance-{instance_id}",
            ports={alertmanager_port: alertmanager_port},
            volumes={
                "alertmanager-data": "/alertmanager",
                "/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/config/alertmanager": "/etc/alertmanager"
            },
            network="monitoring-bridge",
            memory="128m",
            memory_reservation="64m",
            cpus=0.3,
            restart="unless-stopped",
            command=[
                "--config.file=/etc/alertmanager/alertmanager_config.yaml",
                "--storage.path=/alertmanager",
                f"--web.external-url=http://localhost:{alertmanager_port}",
                "--cluster.listen-address="
            ],
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    f"wget --no-verbose --tries=1 --spider http://localhost:{alertmanager_port}/-/healthy || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )

        logger.info(
            "event=alertmanager_manager_init service=alertmanager instance=%s port=%s",
            instance_id, alertmanager_port
        )

        super().__init__(config)

    def reload_config(self) -> bool:
        command = "killall -HUP alertmanager"
        exit_code, output = self.exec(command)

        if exit_code != 0:
            logger.error(
                "event=alertmanager_reload_failed output=%s exit_code=%s",
                output, exit_code
            )
            return False

        logger.info("event=alertmanager_reload_success")
        return True

    def check_config(self) -> Dict[str, Any]:
        command = "amtool check-config /etc/alertmanager/alertmanager_config.yaml"
        exit_code, output = self.exec(command)

        logger.info(
            "event=alertmanager_config_validation exit_code=%s",
            exit_code
        )

        return {
            "valid": exit_code == 0,
            "output": output
        }

    def test_slack_webhook(self) -> Dict[str, Any]:
        command = (
            'amtool alert add test_alert '
            'alertname="TestAlert" '
            'severity="info" '
            'summary="Test alert from Alertmanager" '
            '--end=5m '
            '--alertmanager.url=http://localhost:$(printenv ALERTMANAGER_PORT)'
        )
        exit_code, output = self.exec(command)

        logger.info(
            "event=alertmanager_slack_test exit_code=%s",
            exit_code
        )

        return {
            "success": exit_code == 0,
            "output": output
        }


@activity.defn
async def start_alertmanager_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=alertmanager_start params=%s", params)
    manager = AlertmanagerManager()
    manager.run()
    logger.info("event=alertmanager_started")
    return True


@activity.defn
async def stop_alertmanager_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=alertmanager_stop_begin")
    manager = AlertmanagerManager()
    manager.stop(timeout=30)
    logger.info("event=alertmanager_stop_complete")
    return True


@activity.defn
async def restart_alertmanager_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=alertmanager_restart_begin")
    manager = AlertmanagerManager()
    manager.restart()
    logger.info("event=alertmanager_restart_complete")
    return True


@activity.defn
async def delete_alertmanager_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=alertmanager_delete_begin")
    manager = AlertmanagerManager()
    manager.delete(force=False)
    logger.info("event=alertmanager_delete_complete")
    return True


@activity.defn
async def reload_alertmanager_config_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=alertmanager_reload_activity_begin")
    manager = AlertmanagerManager()
    result = manager.reload_config()

    if result:
        logger.info("event=alertmanager_reload_activity_success")
    else:
        logger.error("event=alertmanager_reload_activity_failed")

    return result


@activity.defn
async def validate_alertmanager_config_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("event=alertmanager_validate_config_begin")
    manager = AlertmanagerManager()
    result = manager.check_config()
    logger.info("event=alertmanager_validate_config_result valid=%s", result["valid"])
    return result


@activity.defn
async def test_slack_integration_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("event=alertmanager_slack_test_begin")
    manager = AlertmanagerManager()
    result = manager.test_slack_webhook()
    logger.info("event=alertmanager_slack_test_result success=%s", result["success"])
    return result
