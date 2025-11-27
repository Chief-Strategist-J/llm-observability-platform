from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class JaegerManager(YAMLBaseService):
    SERVICE_NAME = "Jaeger"
    SERVICE_DESCRIPTION = "jaeger service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="jaeger", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        jaeger_port = pm.get_port("jaeger", instance_id, "ui_port")
        self._port = jaeger_port
        self._instance_id = instance_id
        
        if not JaegerManager._yaml_file_cache:
            JaegerManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "jaeger-dynamic-docker.yaml"
        
        env_vars = {
            "JAEGER_UI_PORT": str(jaeger_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(JaegerManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=JaegerManager._yaml_file_cache,
            service_name="jaeger",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="jaeger", instance=instance_id, port=jaeger_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_jaeger")
async def start_jaeger_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_jaeger", instance=instance_id)
    JaegerManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_jaeger", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_jaeger")
async def stop_jaeger_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_jaeger", instance=instance_id)
    JaegerManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_jaeger", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_jaeger")
async def restart_jaeger_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_jaeger", instance=instance_id)
    JaegerManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_jaeger", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_jaeger")
async def delete_jaeger_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_jaeger", instance=instance_id)
    JaegerManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_jaeger", instance=instance_id)
    return True
