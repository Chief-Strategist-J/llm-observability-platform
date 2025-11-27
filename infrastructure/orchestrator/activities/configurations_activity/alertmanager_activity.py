from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class AlertmanagerManager(YAMLBaseService):
    SERVICE_NAME = "Alertmanager"
    SERVICE_DESCRIPTION = "alertmanager service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="alertmanager", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        alertmanager_port = pm.get_port("alertmanager", instance_id, "port")
        self._port = alertmanager_port
        self._instance_id = instance_id
        
        if not AlertmanagerManager._yaml_file_cache:
            AlertmanagerManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "alertmanager-docker.yaml"
        
        env_vars = {
            "ALERTMANAGER_PORT": str(alertmanager_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(AlertmanagerManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=AlertmanagerManager._yaml_file_cache,
            service_name="alertmanager",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="alertmanager", instance=instance_id, port=alertmanager_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_alertmanager")
async def start_alertmanager_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_alertmanager", instance=instance_id)
    AlertmanagerManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_alertmanager", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_alertmanager")
async def stop_alertmanager_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_alertmanager", instance=instance_id)
    AlertmanagerManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_alertmanager", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_alertmanager")
async def restart_alertmanager_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_alertmanager", instance=instance_id)
    AlertmanagerManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_alertmanager", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_alertmanager")
async def delete_alertmanager_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_alertmanager", instance=instance_id)
    AlertmanagerManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_alertmanager", instance=instance_id)
    return True
