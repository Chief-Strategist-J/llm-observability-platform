from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class TraefikManager(YAMLBaseService):
    SERVICE_NAME = "Traefik"
    SERVICE_DESCRIPTION = "traefik service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="traefik", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        traefik_port = pm.get_port("traefik", instance_id, "http_port")
        grafana_port = pm.get_port("grafana", instance_id, "port")
        loki_port = pm.get_port("loki", instance_id, "port")
        otel_port = pm.get_port("otel", instance_id, "port")
        self._port = traefik_port
        self._instance_id = instance_id
        
        if not TraefikManager._yaml_file_cache:
            TraefikManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "traefik-dynamic-docker.yaml"
        
        env_vars = {
            "HTTP_PORT": str(traefik_port),
            "GRAFANA_PORT": str(grafana_port),
            "LOKI_PORT": str(loki_port),
            "OTEL_PORT": str(otel_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(TraefikManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=TraefikManager._yaml_file_cache,
            service_name="traefik",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="traefik", instance=instance_id, port=traefik_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_traefik")
async def start_traefik_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_traefik", instance=instance_id)
    TraefikManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_traefik", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_traefik")
async def stop_traefik_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_traefik", instance=instance_id)
    TraefikManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_traefik", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_traefik")
async def restart_traefik_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_traefik", instance=instance_id)
    TraefikManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_traefik", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_traefik")
async def delete_traefik_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_traefik", instance=instance_id)
    TraefikManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_traefik", instance=instance_id)
    return True
