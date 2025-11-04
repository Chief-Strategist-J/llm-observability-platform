import logging
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class PrometheusManager(BaseService):
    SERVICE_NAME = "Prometheus"
    SERVICE_DESCRIPTION = "metrics collection and monitoring"
    DEFAULT_PORT = 9090
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self):
        config = ContainerConfig(
            image="prom/prometheus:latest",
            name="prometheus-development",
            ports={9090: 9090},
            volumes={
                "prometheus-data": "/prometheus",
                "prometheus-config": "/etc/prometheus"
            },
            network="observability-network",
            memory="512m",
            memory_reservation="256m",
            cpus=1.0,
            restart="unless-stopped",
            command=[
                "--config.file=/etc/prometheus/prometheus.yml",
                "--storage.tsdb.path=/prometheus"
            ],
            healthcheck={
                "test": ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1"],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )
        super().__init__(config)


@activity.defn
async def start_prometheus_activity(service_name: str) -> bool:
    try:
        manager = PrometheusManager()
        manager.run()
        return True
    except Exception as e:
        logger.error("Failed to start Prometheus service: %s", e, exc_info=True)
        return False


@activity.defn
async def stop_prometheus_activity(service_name: str) -> bool:
    try:
        manager = PrometheusManager()
        manager.stop(timeout=30)
        return True
    except Exception as e:
        logger.error("Failed to stop Prometheus service: %s", e, exc_info=True)
        return False


@activity.defn
async def restart_prometheus_activity(service_name: str) -> bool:
    try:
        manager = PrometheusManager()
        manager.restart()
        return True
    except Exception as e:
        logger.error("Failed to restart Prometheus service: %s", e, exc_info=True)
        return False


@activity.defn
async def delete_prometheus_activity(service_name: str, force: bool = False) -> bool:
    try:
        manager = PrometheusManager()
        manager.delete(force=force)
        return True
    except Exception as e:
        logger.error("Failed to delete Prometheus service: %s", e, exc_info=True)
        return False
