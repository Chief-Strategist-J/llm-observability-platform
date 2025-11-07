import logging
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class OpenTelemetryCollectorManager(BaseService):
    SERVICE_NAME = "OpenTelemetry Collector"
    SERVICE_DESCRIPTION = "telemetry data collection and processing"
    DEFAULT_PORT = 13133
    HEALTH_CHECK_TIMEOUT = 60

    def __init__(self):
        config = ContainerConfig(
            image="otel/opentelemetry-collector-contrib:latest",
            name="opentelemetry-collector-development",
            ports={
                4317: 4317,
                4318: 4318,
                13133: 13133,
                8888: 8888,
                8889: 8889
            },
            volumes={
                "otel-config": "/etc/otelcol",
                "otel-data": "/var/lib/otelcol",
                "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "ro"},
                "/var/log/application": {"bind": "/var/log/application", "mode": "ro"},
                "/var/log/infrastructure": {"bind": "/var/log/infrastructure", "mode": "ro"}
            },
            network="observability-network",
            memory="512m",
            memory_reservation="256m",
            cpus=0.5,
            restart="unless-stopped",
            environment={"OTEL_LOG_LEVEL": "INFO"},
            command=[
                "--config=/etc/otelcol/telemetry.yaml",
                "--config-dir=/etc/otelcol"
            ],
            healthcheck={
                "test": ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:13133/ || exit 1"],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 60000000000
            }
        )
        super().__init__(config)

    def get_metrics(self) -> str:
        command = 'wget -qO- "http://localhost:8888/metrics"'
        exit_code, output = self.exec(command)
        if exit_code != 0:
            logger.error("Failed to get metrics: %s", output)
            return ""
        return output


@activity.defn
async def start_opentelemetry_collector(service_name: str) -> bool:
    try:
        manager = OpenTelemetryCollectorManager()
        manager.run()
        return True
    except Exception as e:
        logger.error("Failed to start OpenTelemetry Collector: %s", e, exc_info=True)
        return False


@activity.defn
async def stop_opentelemetry_collector(service_name: str) -> bool:
    try:
        manager = OpenTelemetryCollectorManager()
        manager.stop(timeout=30)
        return True
    except Exception as e:
        logger.error("Failed to stop OpenTelemetry Collector: %s", e, exc_info=True)
        return False


@activity.defn
async def restart_opentelemetry_collector(service_name: str) -> bool:
    try:
        manager = OpenTelemetryCollectorManager()
        manager.restart()
        return True
    except Exception as e:
        logger.error("Failed to restart OpenTelemetry Collector: %s", e, exc_info=True)
        return False


@activity.defn
async def delete_opentelemetry_collector(service_name: str, force: bool = False) -> bool:
    try:
        manager = OpenTelemetryCollectorManager()
        manager.delete(force=force)
        return True
    except Exception as e:
        logger.error("Failed to delete OpenTelemetry Collector: %s", e, exc_info=True)
        return False
