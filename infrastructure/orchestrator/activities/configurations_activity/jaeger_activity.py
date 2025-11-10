import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class JaegerManager(BaseService):
    SERVICE_NAME = "Jaeger"
    SERVICE_DESCRIPTION = "distributed tracing service"
    DEFAULT_PORT = 16686
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self):
        config = ContainerConfig(
            image="jaegertracing/all-in-one:latest",
            name="jaeger-development",
            ports={
                16686: 16686,
                4317: 4317,
                4318: 4318,
                14250: 14250,
                14268: 14268,
                9411: 9411,
            },
            volumes={"jaeger-data": "/tmp"},
            network="observability-network",
            memory="512m",
            memory_reservation="256m",
            cpus=0.5,
            restart="unless-stopped",
            environment={
                "COLLECTOR_OTLP_ENABLED": "true",
                "COLLECTOR_ZIPKIN_HOST_PORT": ":9411",
            },
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "wget --no-verbose --tries=1 --spider http://localhost:16686/ || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )
        super().__init__(config)

    def get_services(self) -> str:
        cmd = 'wget -qO- "http://localhost:16686/api/services"'
        code, out = self.exec(cmd)
        if code != 0:
            logger.error("Failed to get services: %s", out)
            return ""
        return out


@activity.defn
async def start_jaeger_activity(params: Dict[str, Any]) -> bool:
    manager = JaegerManager()
    manager.run()
    return True


@activity.defn
async def stop_jaeger_activity(params: Dict[str, Any]) -> bool:
    manager = JaegerManager()
    manager.stop(timeout=30)
    return True


@activity.defn
async def restart_jaeger_activity(params: Dict[str, Any]) -> bool:
    manager = JaegerManager()
    manager.restart()
    return True


@activity.defn
async def delete_jaeger_activity(params: Dict[str, Any]) -> bool:
    manager = JaegerManager()
    manager.delete(force=False)
    return True
