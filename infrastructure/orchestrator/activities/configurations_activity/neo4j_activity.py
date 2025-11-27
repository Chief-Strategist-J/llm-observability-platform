from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class Neo4jManager(YAMLBaseService):
    SERVICE_NAME = "Neo4j"
    SERVICE_DESCRIPTION = "neo4j service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="neo4j", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        neo4j_port = pm.get_port("neo4j", instance_id, "http_port")
        bolt_port = pm.get_port("neo4j", instance_id, "bolt_port")
        self._port = neo4j_port
        self._instance_id = instance_id
        
        if not Neo4jManager._yaml_file_cache:
            Neo4jManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "neo4j-dynamic-docker.yaml"
        
        env_vars = {
            "NEO4J_HTTP_PORT": str(neo4j_port),
            "NEO4J_BOLT_PORT": str(bolt_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(Neo4jManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=Neo4jManager._yaml_file_cache,
            service_name="neo4j",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="neo4j", instance=instance_id, port=neo4j_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_neo4j")
async def start_neo4j_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_neo4j", instance=instance_id)
    Neo4jManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_neo4j", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_neo4j")
async def stop_neo4j_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_neo4j", instance=instance_id)
    Neo4jManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_neo4j", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_neo4j")
async def restart_neo4j_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_neo4j", instance=instance_id)
    Neo4jManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_neo4j", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_neo4j")
async def delete_neo4j_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_neo4j", instance=instance_id)
    Neo4jManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_neo4j", instance=instance_id)
    return True
