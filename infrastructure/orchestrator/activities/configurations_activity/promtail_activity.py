from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class PromtailManager(YAMLBaseService):
    SERVICE_NAME = "Promtail"
    SERVICE_DESCRIPTION = "promtail service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="promtail", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        promtail_port = pm.get_port("promtail", instance_id, "http_port")
        self._port = promtail_port
        self._instance_id = instance_id
        
        if not PromtailManager._yaml_file_cache:
            PromtailManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "promtail-dynamic-docker.yaml"
        
        env_vars = {
            "PROMTAIL_PORT": str(promtail_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(PromtailManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=PromtailManager._yaml_file_cache,
            service_name="promtail",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="promtail", instance=instance_id, port=promtail_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_promtail")
async def start_promtail_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_promtail", instance=instance_id)
    PromtailManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_promtail", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_promtail")
async def stop_promtail_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_promtail", instance=instance_id)
    PromtailManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_promtail", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_promtail")
async def restart_promtail_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_promtail", instance=instance_id)
    PromtailManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_promtail", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_promtail")
async def delete_promtail_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_promtail", instance=instance_id)
    PromtailManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_promtail", instance=instance_id)
    return True
