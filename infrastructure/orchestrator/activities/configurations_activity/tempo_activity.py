from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class TempoManager(YAMLBaseService):
    SERVICE_NAME = "Tempo"
    SERVICE_DESCRIPTION = "tempo service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="tempo", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        tempo_port = pm.get_port("tempo", instance_id, "http_port")
        self._port = tempo_port
        self._instance_id = instance_id
        
        if not TempoManager._yaml_file_cache:
            TempoManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "tempo-dynamic-docker.yaml"
        
        env_vars = {
            "TEMPO_PORT": str(tempo_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(TempoManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=TempoManager._yaml_file_cache,
            service_name="tempo",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="tempo", instance=instance_id, port=tempo_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_tempo")
async def start_tempo_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_tempo", instance=instance_id)
    TempoManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_tempo", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_tempo")
async def stop_tempo_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_tempo", instance=instance_id)
    TempoManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_tempo", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_tempo")
async def restart_tempo_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_tempo", instance=instance_id)
    TempoManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_tempo", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_tempo")
async def delete_tempo_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_tempo", instance=instance_id)
    TempoManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_tempo", instance=instance_id)
    return True
