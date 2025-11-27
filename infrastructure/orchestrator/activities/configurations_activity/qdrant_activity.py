from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class QdrantManager(YAMLBaseService):
    SERVICE_NAME = "Qdrant"
    SERVICE_DESCRIPTION = "qdrant service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="qdrant", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        qdrant_port = pm.get_port("qdrant", instance_id, "http_port")
        grpc_port = pm.get_port("qdrant", instance_id, "grpc_port")
        self._port = qdrant_port
        self._instance_id = instance_id
        
        if not QdrantManager._yaml_file_cache:
            QdrantManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "qdrant-dynamic-docker.yaml"
        
        env_vars = {
            "QDRANT_HTTP_PORT": str(qdrant_port),
            "QDRANT_GRPC_PORT": str(grpc_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(QdrantManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=QdrantManager._yaml_file_cache,
            service_name="qdrant",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="qdrant", instance=instance_id, port=qdrant_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_qdrant")
async def start_qdrant_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_qdrant", instance=instance_id)
    QdrantManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_qdrant", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_qdrant")
async def stop_qdrant_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_qdrant", instance=instance_id)
    QdrantManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_qdrant", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_qdrant")
async def restart_qdrant_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_qdrant", instance=instance_id)
    QdrantManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_qdrant", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_qdrant")
async def delete_qdrant_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_qdrant", instance=instance_id)
    QdrantManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_qdrant", instance=instance_id)
    return True
