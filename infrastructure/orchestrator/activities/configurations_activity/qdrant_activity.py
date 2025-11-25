import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class QdrantManager(BaseService):
    SERVICE_NAME = "Qdrant"
    SERVICE_DESCRIPTION = "vector database"
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0):
        pm = get_port_manager()

        http_port = pm.get_port("qdrant", instance_id, "http_port")
        grpc_port = pm.get_port("qdrant", instance_id, "grpc_port")

        config = ContainerConfig(
            image="qdrant/qdrant:latest",
            name=f"qdrant-instance-{instance_id}",
            ports={
                http_port: http_port,
                grpc_port: grpc_port
            },
            volumes={
                "qdrant-storage": "/qdrant/storage",
                "qdrant-snapshots": "/qdrant/snapshots"
            },
            network="data-network",
            memory="512m",
            memory_reservation="256m",
            cpus=0.5,
            restart="unless-stopped",
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
            "event=qdrant_manager_init service=qdrant instance=%s http_port=%s grpc_port=%s",
            instance_id, http_port, grpc_port
        )

        super().__init__(config)


@activity.defn
async def start_qdrant_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=qdrant_start params=%s", params)
    QdrantManager().run()
    logger.info("event=qdrant_started")
    return True


@activity.defn
async def stop_qdrant_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=qdrant_stop_begin")
    QdrantManager().stop(timeout=30)
    logger.info("event=qdrant_stop_complete")
    return True


@activity.defn
async def restart_qdrant_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=qdrant_restart_begin")
    QdrantManager().restart()
    logger.info("event=qdrant_restart_complete")
    return True


@activity.defn
async def delete_qdrant_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=qdrant_delete_begin")
    QdrantManager().delete(force=False)
    logger.info("event=qdrant_delete_complete")
    return True
