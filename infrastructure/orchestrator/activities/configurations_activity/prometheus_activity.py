import logging
from pathlib import Path
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
        dynamic_dir = Path("/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig")
        dynamic_dir.mkdir(parents=True, exist_ok=True)
        
        prometheus_config = dynamic_dir / "prometheus.yml"
        if not prometheus_config.exists():
            default_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['opentelemetry-collector-development:8888']
"""
            prometheus_config.write_text(default_config, encoding="utf-8")
            logger.info("prometheus_config_created path=%s", prometheus_config)

        config = ContainerConfig(
            image="prom/prometheus:latest",
            name="prometheus-development",
            ports={},
            volumes={
                "prometheus-data": {"bind": "/prometheus", "mode": "rw"},
                str(prometheus_config.absolute()): {"bind": "/etc/prometheus/prometheus.yml", "mode": "ro"},
            },
            network="observability-network",
            memory="512m",
            memory_reservation="256m",
            cpus=1.0,
            restart="unless-stopped",
            command=[
                "--config.file=/etc/prometheus/prometheus.yml",
                "--storage.tsdb.path=/prometheus",
                "--web.enable-remote-write-receiver",
                "--enable-feature=exemplar-storage"
            ],
            labels={
                "traefik.enable": "true",
                "traefik.http.routers.prometheus.rule": "PathPrefix(`/`)",
                "traefik.http.routers.prometheus.entrypoints": "prometheus",
                "traefik.http.routers.prometheus.service": "prometheus",
                "traefik.http.services.prometheus.loadbalancer.server.port": "9090",
                "traefik.docker.network": "observability-network",
            },
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1"
                ],
                "interval": 30_000_000_000,
                "timeout": 10_000_000_000,
                "retries": 3,
                "start_period": 40_000_000_000
            }
        )
        super().__init__(config)


@activity.defn
async def start_prometheus_activity(params: Dict[str, Any]) -> bool:
    logger.info("prometheus_start_activity_called")
    PrometheusManager().run()
    logger.info("prometheus_started")
    return True


@activity.defn
async def stop_prometheus_activity(params: Dict[str, Any]) -> bool:
    logger.info("prometheus_stop_activity_called")
    PrometheusManager().stop(timeout=30)
    logger.info("prometheus_stopped")
    return True


@activity.defn
async def restart_prometheus_activity(params: Dict[str, Any]) -> bool:
    logger.info("prometheus_restart_activity_called")
    PrometheusManager().restart()
    logger.info("prometheus_restarted")
    return True


@activity.defn
async def delete_prometheus_activity(params: Dict[str, Any]) -> bool:
    logger.info("prometheus_delete_activity_called")
    PrometheusManager().delete(force=False)
    logger.info("prometheus_deleted")
    return True