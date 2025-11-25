import logging
from pathlib import Path
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class PrometheusManager(BaseService):
    SERVICE_NAME = "Prometheus"
    SERVICE_DESCRIPTION = "metrics collection and monitoring"
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0):
        pm = get_port_manager()
        host_port = pm.get_port("prometheus", instance_id, "port")

        dynamic_dir = Path("/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig")
        dynamic_dir.mkdir(parents=True, exist_ok=True)

        prometheus_config = dynamic_dir / f"prometheus-{instance_id}.yml"

        if not prometheus_config.exists():
            default_config = f"""global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:{host_port}']

  - job_name: 'otel-collector'
    static_configs:
      - targets: ['opentelemetry-collector-development:8888']
"""
            prometheus_config.write_text(default_config, encoding="utf-8")

            logger.info(
                "event=prometheus_config_created path=%s instance=%s",
                prometheus_config, instance_id
            )

        config = ContainerConfig(
            image="prom/prometheus:latest",
            name=f"prometheus-instance-{instance_id}",
            ports={host_port: host_port},
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
                "traefik.docker.network": "observability-network"
            },
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    f"wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )

        logger.info(
            "event=prometheus_manager_init service=prometheus instance=%s port=%s config_file=%s",
            instance_id, host_port, prometheus_config
        )

        super().__init__(config)


@activity.defn
async def start_prometheus_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=prometheus_start params=%s", params)
    PrometheusManager().run()
    logger.info("event=prometheus_started")
    return True


@activity.defn
async def stop_prometheus_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=prometheus_stop_begin")
    PrometheusManager().stop(timeout=30)
    logger.info("event=prometheus_stop_complete")
    return True


@activity.defn
async def restart_prometheus_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=prometheus_restart_begin")
    PrometheusManager().restart()
    logger.info("event=prometheus_restart_complete")
    return True


@activity.defn
async def delete_prometheus_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=prometheus_delete_begin")
    PrometheusManager().delete(force=False)
    logger.info("event=prometheus_delete_complete")
    return True
