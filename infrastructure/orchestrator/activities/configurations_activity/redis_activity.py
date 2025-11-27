from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class RedisManager(YAMLBaseService):
    SERVICE_NAME = "Redis"
    SERVICE_DESCRIPTION = "in-memory data store"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="redis", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        redis_port = pm.get_port("redis", instance_id, "port")
        self._port = redis_port
        self._instance_id = instance_id
        
        if not RedisManager._yaml_file_cache:
            RedisManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "redis-dynamic-docker.yaml"
        
        env_vars = {
            "REDIS_PORT": str(redis_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(RedisManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=RedisManager._yaml_file_cache,
            service_name="redis",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="redis", instance=instance_id, port=redis_port, container=self.config.container_name)
    
    def ping(self) -> bool:
        log.debug("redis_ping_start", instance=self._instance_id, port=self._port)
        port = list(self.config.ports.values())[0]
        code, out = self.exec(f"redis-cli -p {port} ping")
        success = code == 0 and "PONG" in out
        log.debug("redis_ping_complete", instance=self._instance_id, success=success)
        return success
    
    def get_info(self) -> str:
        log.debug("redis_info_start", instance=self._instance_id)
        port = list(self.config.ports.values())[0]
        code, out = self.exec(f"redis-cli -p {port} INFO")
        log.debug("redis_info_complete", instance=self._instance_id, exit_code=code)
        return out if code == 0 else ""
    
    def flush_all(self) -> bool:
        log.info("redis_flushall_start", instance=self._instance_id, port=self._port)
        port = list(self.config.ports.values())[0]
        code, out = self.exec(f"redis-cli -p {port} FLUSHALL")
        success = code == 0 and "OK" in out
        log.info("redis_flushall_complete", instance=self._instance_id, success=success)
        return success

@activity.defn
@trace_operation("start_redis")
async def start_redis_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_redis", instance=instance_id)
    RedisManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_redis", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_redis")
async def stop_redis_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_redis", instance=instance_id)
    RedisManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_redis", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_redis")
async def restart_redis_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_redis", instance=instance_id)
    RedisManager(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_redis", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_redis")
async def delete_redis_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_redis", instance=instance_id)
    RedisManager(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_redis", instance=instance_id)
    return True
