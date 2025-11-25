import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class QdrantManager(BaseService):
    SERVICE_NAME = "Qdrant"
    SERVICE_DESCRIPTION = "vector database"
    DEFAULT_PORT = 6333
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0):
        pm = get_port_manager()
            http_port = pm.get_port("qdrant", instance_id, "http_port")
            grpc_port = pm.get_port("qdrant", instance_id, "grpc_port")
            config = ContainerConfig(
                image="qdrant/qdrant:latest",
                name="qdrant-development",
                ports={
                    6333: http_port,
                    6334: grpc_port,
                },
            volumes={
                "qdrant-storage": "/qdrant/storage",
                "qdrant-snapshots": "/qdrant/snapshots",
            },
            network="data-network",
            memory="512m",
            memory_reservation="256m",
            cpus=0.5,
            restart="unless-stopped",
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "wget --no-verbose --tries=1 --spider http://localhost:6333/ || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000,
            },
        )
        super().__init__(config)


@activity.defn
async def start_qdrant_activity(params: Dict[str, Any]) -> bool:
    QdrantManager().run()
    return True


@activity.defn
async def stop_qdrant_activity(params: Dict[str, Any]) -> bool:
    QdrantManager().stop(timeout=30)
    return True


@activity.defn
async def restart_qdrant_activity(params: Dict[str, Any]) -> bool:
    QdrantManager().restart()
    return True


@activity.defn
async def delete_qdrant_activity(params: Dict[str, Any]) -> bool:
    QdrantManager().delete(force=False)
    return True
