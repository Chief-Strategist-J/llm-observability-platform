from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class MongoExpressManager(YAMLBaseService):
    SERVICE_NAME = "MongoExpress"
    SERVICE_DESCRIPTION = "mongoexpress service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="mongoexpress", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        mongoexpress_port = pm.get_port("mongoexpress", instance_id, "port")
        self._port = mongoexpress_port
        self._instance_id = instance_id
        
        if not MongoExpressManager._yaml_file_cache:
            MongoExpressManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "mongoexpress-dynamic-docker.yaml"
        
        env_vars = {
            "MONGOEXPRESS_PORT": str(mongoexpress_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(MongoExpressManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=MongoExpressManager._yaml_file_cache,
            service_name="mongoexpress",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="mongoexpress", instance=instance_id, port=mongoexpress_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_mongoexpress")
async def start_mongoexpress_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_mongoexpress", instance=instance_id)
    MongoExpressManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_mongoexpress", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_mongoexpress")
async def stop_mongoexpress_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_mongoexpress", instance=instance_id)
    MongoExpressManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_mongoexpress", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_mongoexpress")
async def restart_mongoexpress_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_mongoexpress", instance=instance_id)
    MongoExpressManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_mongoexpress", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_mongoexpress")
async def delete_mongoexpress_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_mongoexpress", instance=instance_id)
    MongoExpressManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_mongoexpress", instance=instance_id)
    return True
