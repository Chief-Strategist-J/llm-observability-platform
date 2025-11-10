import logging
from typing import Dict, Any
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
                "test": [
                    "CMD-SHELL",
                    "wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )
        super().__init__(config)


@activity.defn
async def start_prometheus_activity(params: Dict[str, Any]) -> bool:
    PrometheusManager().run()
    return True


@activity.defn
async def stop_prometheus_activity(params: Dict[str, Any]) -> bool:
    PrometheusManager().stop(timeout=30)
    return True


@activity.defn
async def restart_prometheus_activity(params: Dict[str, Any]) -> bool:
    PrometheusManager().restart()
    return True


@activity.defn
async def delete_prometheus_activity(params: Dict[str, Any]) -> bool:
    PrometheusManager().delete(force=False)
    return True
