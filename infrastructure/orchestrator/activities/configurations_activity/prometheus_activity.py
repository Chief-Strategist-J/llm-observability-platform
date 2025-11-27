from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class PrometheusManager(YAMLBaseService):
    SERVICE_NAME = "Prometheus"
    SERVICE_DESCRIPTION = "prometheus service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="prometheus", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        prometheus_port = pm.get_port("prometheus", instance_id, "port")
        self._port = prometheus_port
        self._instance_id = instance_id
        
        if not PrometheusManager._yaml_file_cache:
            PrometheusManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "prometheus-dynamic-docker.yaml"
        
        env_vars = {
            "PROMETHEUS_PORT": str(prometheus_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(PrometheusManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=PrometheusManager._yaml_file_cache,
            service_name="prometheus",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="prometheus", instance=instance_id, port=prometheus_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_prometheus")
async def start_prometheus_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_prometheus", instance=instance_id)
    PrometheusManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_prometheus", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_prometheus")
async def stop_prometheus_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_prometheus", instance=instance_id)
    PrometheusManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_prometheus", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_prometheus")
async def restart_prometheus_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_prometheus", instance=instance_id)
    PrometheusManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_prometheus", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_prometheus")
async def delete_prometheus_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_prometheus", instance=instance_id)
    PrometheusManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_prometheus", instance=instance_id)
    return True
