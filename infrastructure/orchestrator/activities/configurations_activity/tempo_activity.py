import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class TempoManager(BaseService):
    SERVICE_NAME = "Tempo"
    SERVICE_DESCRIPTION = "distributed tracing backend"
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0):
        pm = get_port_manager()

        http_port = pm.get_port("tempo", instance_id, "http_port")
        otlp_grpc_port = pm.get_port("tempo", instance_id, "otlp_grpc_port")
        otlp_http_port = pm.get_port("tempo", instance_id, "otlp_http_port")
        grpc_port = pm.get_port("tempo", instance_id, "grpc_port")
        zipkin_port = pm.get_port("tempo", instance_id, "zipkin_port")

        ports = {
            http_port: 3200,          # Tempo HTTP API
            otlp_grpc_port: 4317,     # OTLP gRPC receiver
            otlp_http_port: 4318,     # OTLP HTTP receiver
            grpc_port: 9095,          # Tempo gRPC API
            zipkin_port: 9411         # Zipkin receiver
        }

        config = ContainerConfig(
            image="grafana/tempo:latest",
            name=f"tempo-instance-{instance_id}",
            ports=ports,
            volumes={"tempo-data": "/tmp/tempo"},
            network="observability-network",
            memory="512m",
            memory_reservation="256m",
            cpus=0.5,
            restart="unless-stopped",
            environment={
                "TEMPO_HTTP_PORT": str(http_port),
            },
            command=[
                "-config.file=/etc/tempo.yaml"
            ],
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    f"wget --no-verbose --tries=1 --spider http://localhost:3200/ready || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )

        logger.info(
            "event=tempo_manager_init service=tempo instance=%s http_port=%s otlp_grpc=%s otlp_http=%s grpc=%s zipkin=%s",
            instance_id, http_port, otlp_grpc_port, otlp_http_port, grpc_port, zipkin_port
        )

        super().__init__(config)

    def get_metrics(self) -> str:
        cmd = 'wget -qO- "http://localhost:3200/metrics"'
        exit_code, output = self.exec(cmd)

        if exit_code != 0:
            logger.error("event=tempo_get_metrics_failed output=%s", output)
            return ""

        logger.info("event=tempo_get_metrics_success")
        return output


@activity.defn
async def start_tempo_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=tempo_start params=%s", params)
    manager = TempoManager()
    manager.run()
    logger.info("event=tempo_started")
    return True


@activity.defn
async def stop_tempo_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=tempo_stop_begin")
    manager = TempoManager()
    manager.stop(timeout=30)
    logger.info("event=tempo_stop_complete")
    return True


@activity.defn
async def restart_tempo_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=tempo_restart_begin")
    manager = TempoManager()
    manager.restart()
    logger.info("event=tempo_restart_complete")
    return True


@activity.defn
async def delete_tempo_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=tempo_delete_begin")
    manager = TempoManager()
    manager.delete(force=False)
    logger.info("event=tempo_delete_complete")
    return True
