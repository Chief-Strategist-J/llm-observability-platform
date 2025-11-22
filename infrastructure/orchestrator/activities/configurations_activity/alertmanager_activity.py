import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class AlertmanagerManager(BaseService):
    SERVICE_NAME = "Alertmanager"
    SERVICE_DESCRIPTION = "alert routing and management"
    DEFAULT_PORT = 9093
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self):
        config = ContainerConfig(
            image="prom/alertmanager:latest",
            name="alertmanager-development",
            ports={9093: 9093},
            volumes={
                "alertmanager-data": "/alertmanager",
                # Mount config directory from your project
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
                "--web.external-url=http://localhost:9093",
                "--cluster.listen-address=",
            ],
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "wget --no-verbose --tries=1 --spider http://localhost:9093/-/healthy || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )
        super().__init__(config)

    def reload_config(self) -> bool:
        """Hot reload Alertmanager config without restart"""
        command = "killall -HUP alertmanager"
        exit_code, output = self.exec(command)
        if exit_code != 0:
            logger.error("Failed to reload Alertmanager config: %s", output)
            return False
        logger.info("Alertmanager config reloaded successfully")
        return True

    def check_config(self) -> Dict[str, Any]:
        """Validate Alertmanager configuration"""
        command = "amtool check-config /etc/alertmanager/alertmanager_config.yaml"
        exit_code, output = self.exec(command)
        return {
            "valid": exit_code == 0,
            "output": output
        }

    def test_slack_webhook(self) -> Dict[str, Any]:
        """Test Slack webhook by sending test alert"""
        command = (
            'amtool alert add test_alert '
            'alertname="TestAlert" '
            'severity="info" '
            'summary="Test alert from Alertmanager" '
            '--end=5m '
            '--alertmanager.url=http://localhost:9093'
        )
        exit_code, output = self.exec(command)
        return {
            "success": exit_code == 0,
            "output": output
        }


@activity.defn
async def start_alertmanager_activity(params: Dict[str, Any]) -> bool:
    """Start Alertmanager container"""
    logger.info("Starting Alertmanager activity with params: %s", params)
    manager = AlertmanagerManager()
    manager.run()
    logger.info("Alertmanager container started successfully")
    return True


@activity.defn
async def stop_alertmanager_activity(params: Dict[str, Any]) -> bool:
    """Stop Alertmanager container"""
    logger.info("Stopping Alertmanager activity")
    manager = AlertmanagerManager()
    manager.stop(timeout=30)
    logger.info("Alertmanager container stopped successfully")
    return True


@activity.defn
async def restart_alertmanager_activity(params: Dict[str, Any]) -> bool:
    """Restart Alertmanager container"""
    logger.info("Restarting Alertmanager activity")
    manager = AlertmanagerManager()
    manager.restart()
    logger.info("Alertmanager container restarted successfully")
    return True


@activity.defn
async def delete_alertmanager_activity(params: Dict[str, Any]) -> bool:
    """Delete Alertmanager container"""
    logger.info("Deleting Alertmanager activity")
    manager = AlertmanagerManager()
    manager.delete(force=False)
    logger.info("Alertmanager container deleted successfully")
    return True


@activity.defn
async def reload_alertmanager_config_activity(params: Dict[str, Any]) -> bool:
    """Hot reload Alertmanager configuration"""
    logger.info("Reloading Alertmanager config")
    manager = AlertmanagerManager()
    result = manager.reload_config()
    if result:
        logger.info("Alertmanager config reloaded successfully")
    else:
        logger.error("Failed to reload Alertmanager config")
    return result


@activity.defn
async def validate_alertmanager_config_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate Alertmanager configuration file"""
    logger.info("Validating Alertmanager config")
    manager = AlertmanagerManager()
    result = manager.check_config()
    logger.info("Config validation result: %s", result)
    return result


@activity.defn
async def test_slack_integration_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """Send test alert to Slack"""
    logger.info("Testing Slack integration")
    manager = AlertmanagerManager()
    result = manager.test_slack_webhook()
    logger.info("Slack test result: %s", result)
    return result