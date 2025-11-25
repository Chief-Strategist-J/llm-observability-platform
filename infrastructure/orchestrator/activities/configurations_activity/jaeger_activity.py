import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class JaegerManager(BaseService):
    SERVICE_NAME = "Jaeger"
    SERVICE_DESCRIPTION = "distributed tracing service"
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0):
        pm = get_port_manager()

        http_port = pm.get_port("jaeger", instance_id, "http_port")
        otlp_grpc_port = pm.get_port("jaeger", instance_id, "otlp_grpc_port")
        otlp_http_port = pm.get_port("jaeger", instance_id, "otlp_http_port")
        grpc_port = pm.get_port("jaeger", instance_id, "grpc_port")
        admin_port = pm.get_port("jaeger", instance_id, "admin_port")
        zipkin_port = pm.get_port("jaeger", instance_id, "zipkin_port")

        ports = {
            http_port: http_port,
            otlp_grpc_port: otlp_grpc_port,
            otlp_http_port: otlp_http_port,
            grpc_port: grpc_port,
            admin_port: admin_port,
            zipkin_port: zipkin_port
        }

        config = ContainerConfig(
            image="jaegertracing/all-in-one:latest",
            name=f"jaeger-instance-{instance_id}",
            ports=ports,
            volumes={"jaeger-data": "/tmp"},
            network="observability-network",
            memory="512m",
            memory_reservation="256m",
            cpus=0.5,
            restart="unless-stopped",
            environment={
                "COLLECTOR_OTLP_ENABLED": "true",
                "COLLECTOR_ZIPKIN_HOST_PORT": f":{zipkin_port}"
            },
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    f"wget --no-verbose --tries=1 --spider http://localhost:{http_port}/ || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )

        logger.info(
            "event=jaeger_manager_init service=jaeger instance=%s http_port=%s grpc_port=%s otlp_grpc=%s otlp_http=%s admin=%s zipkin=%s",
            instance_id, http_port, grpc_port, otlp_grpc_port, otlp_http_port, admin_port, zipkin_port
        )

        super().__init__(config)

    def get_services(self) -> str:
        cmd = 'wget -qO- "http://localhost:$(printenv JAEGER_HTTP_PORT)/api/services"'
        exit_code, output = self.exec(cmd)

        if exit_code != 0:
            logger.error("event=jaeger_get_services_failed output=%s", output)
            return ""

        logger.info("event=jaeger_get_services_success")
        return output


@activity.defn
async def start_jaeger_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=jaeger_start params=%s", params)
    manager = JaegerManager()
    manager.run()
    logger.info("event=jaeger_started")
    return True


@activity.defn
async def stop_jaeger_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=jaeger_stop_begin")
    manager = JaegerManager()
    manager.stop(timeout=30)
    logger.info("event=jaeger_stop_complete")
    return True


@activity.defn
async def restart_jaeger_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=jaeger_restart_begin")
    manager = JaegerManager()
    manager.restart()
    logger.info("event=jaeger_restart_complete")
    return True


@activity.defn
async def delete_jaeger_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=jaeger_delete_begin")
    manager = JaegerManager()
    manager.delete(force=False)
    logger.info("event=jaeger_delete_complete")
    return True
