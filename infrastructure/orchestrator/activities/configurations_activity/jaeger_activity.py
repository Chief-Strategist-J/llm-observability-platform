import logging
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
                "test": ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:16686/ || exit 1"],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )
        super().__init__(config)

    def get_services(self) -> str:
        command = 'wget -qO- "http://localhost:16686/api/services"'
        exit_code, output = self.exec(command)
        if exit_code != 0:
            logger.error("Failed to get services: %s", output)
            return ""
        return output


@activity.defn
async def start_jaeger_activity(service_name: str) -> bool:
    try:
        manager = JaegerManager()
        manager.run()
        return True
    except Exception as e:
        logger.error("Failed to start Jaeger service: %s", e, exc_info=True)
        return False


@activity.defn
async def stop_jaeger_activity(service_name: str) -> bool:
    try:
        manager = JaegerManager()
        manager.stop(timeout=30)
        return True
    except Exception as e:
        logger.error("Failed to stop Jaeger service: %s", e, exc_info=True)
        return False


@activity.defn
async def restart_jaeger_activity(service_name: str) -> bool:
    try:
        manager = JaegerManager()
        manager.restart()
        return True
    except Exception as e:
        logger.error("Failed to restart Jaeger service: %s", e, exc_info=True)
        return False


@activity.defn
async def delete_jaeger_activity(service_name: str, force: bool = False) -> bool:
    try:
        manager = JaegerManager()
        manager.delete(force=force)
        return True
    except Exception as e:
        logger.error("Failed to delete Jaeger service: %s", e, exc_info=True)
        return False
