from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class LokiManager(YAMLBaseService):
    SERVICE_NAME = "Loki"
    SERVICE_DESCRIPTION = "loki service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="loki", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        loki_port = pm.get_port("loki", instance_id, "http_port")
        self._port = loki_port
        self._instance_id = instance_id
        
        if not LokiManager._yaml_file_cache:
            LokiManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "loki-dynamic-docker.yaml"
        
        env_vars = {
            "LOKI_PORT": str(loki_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(LokiManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=LokiManager._yaml_file_cache,
            service_name="loki",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="loki", instance=instance_id, port=loki_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_loki")
async def start_loki_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_loki", instance=instance_id)
    LokiManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_loki", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_loki")
async def stop_loki_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_loki", instance=instance_id)
    LokiManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_loki", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_loki")
async def restart_loki_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_loki", instance=instance_id)
    LokiManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_loki", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_loki")
async def delete_loki_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_loki", instance=instance_id)
    LokiManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_loki", instance=instance_id)
    return True
