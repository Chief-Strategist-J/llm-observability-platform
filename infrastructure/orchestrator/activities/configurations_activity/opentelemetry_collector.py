from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class OtelCollectorManager(YAMLBaseService):
    SERVICE_NAME = "OtelCollector"
    SERVICE_DESCRIPTION = "otel-collector service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="otel-collector", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        otel-collector_port = pm.get_port("otel-collector", instance_id, "http_port")
        grpc_port = pm.get_port("otel-collector", instance_id, "grpc_port")
        self._port = otel-collector_port
        self._instance_id = instance_id
        
        if not OtelCollectorManager._yaml_file_cache:
            OtelCollectorManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "otel-collector-dynamic-docker.yaml"
        
        env_vars = {
            "OTEL_HTTP_PORT": str(otel-collector_port),
            "OTEL_GRPC_PORT": str(grpc_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(OtelCollectorManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=OtelCollectorManager._yaml_file_cache,
            service_name="otel-collector",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="otel-collector", instance=instance_id, port=otel-collector_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_otel-collector")
async def start_otel-collector_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_otel-collector", instance=instance_id)
    OtelCollectorManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_otel-collector", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_otel-collector")
async def stop_otel-collector_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_otel-collector", instance=instance_id)
    OtelCollectorManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_otel-collector", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_otel-collector")
async def restart_otel-collector_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_otel-collector", instance=instance_id)
    OtelCollectorManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_otel-collector", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_otel-collector")
async def delete_otel-collector_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_otel-collector", instance=instance_id)
    OtelCollectorManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_otel-collector", instance=instance_id)
    return True
