from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class GrafanaManager(YAMLBaseService):
    SERVICE_NAME = "Grafana"
    SERVICE_DESCRIPTION = "grafana service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="grafana", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        grafana_port = pm.get_port("grafana", instance_id, "port")
        self._port = grafana_port
        self._instance_id = instance_id
        
        if not GrafanaManager._yaml_file_cache:
            GrafanaManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "grafana-dynamic-docker.yaml"
        
        env_vars = {
            "GRAFANA_PORT": str(grafana_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(GrafanaManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=GrafanaManager._yaml_file_cache,
            service_name="grafana",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="grafana", instance=instance_id, port=grafana_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_grafana")
async def start_grafana_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_grafana", instance=instance_id)
    GrafanaManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_grafana", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_grafana")
async def stop_grafana_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_grafana", instance=instance_id)
    GrafanaManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_grafana", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_grafana")
async def restart_grafana_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_grafana", instance=instance_id)
    GrafanaManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_grafana", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_grafana")
async def delete_grafana_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_grafana", instance=instance_id)
    GrafanaManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_grafana", instance=instance_id)
    return True
