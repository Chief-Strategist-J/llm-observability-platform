from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class MongoDBManager(YAMLBaseService):
    SERVICE_NAME = "MongoDB"
    SERVICE_DESCRIPTION = "document database"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="mongodb", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        mongo_port = pm.get_port("mongodb", instance_id, "port")
        self._port = mongo_port
        self._instance_id = instance_id
        
        if not MongoDBManager._yaml_file_cache:
            MongoDBManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "mongodb-dynamic-docker.yaml"
        
        env_vars = {
            "MONGO_PORT": str(mongo_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(MongoDBManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=MongoDBManager._yaml_file_cache,
            service_name="mongodb",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="mongodb", instance=instance_id, port=mongo_port, container=self.config.container_name)
    
    def ping(self) -> bool:
        log.debug("mongodb_ping_start", instance=self._instance_id, port=self._port)
        cmd = (
            f"mongosh --quiet --port {self._port} --eval \"db.adminCommand('ping')\" "
            "--username admin --password MongoPassword123! --authenticationDatabase admin"
        )
        code, out = self.exec(cmd)
        success = code == 0 and out and "ok" in out.lower()
        log.debug("mongodb_ping_complete", instance=self._instance_id, success=success)
        return success
    
    def get_server_status(self) -> str:
        log.debug("mongodb_status_start", instance=self._instance_id)
        cmd = (
            f"mongosh --quiet --port {self._port} "
            "--eval \"JSON.stringify(db.serverStatus())\" "
            "--username admin --password MongoPassword123! --authenticationDatabase admin"
        )        
        code, out = self.exec(cmd)
        log.debug("mongodb_status_complete", instance=self._instance_id, exit_code=code)
        return out if code == 0 else ""
    
    def list_databases(self) -> str:
        log.debug("mongodb_list_dbs_start", instance=self._instance_id)
        cmd = (
            f"mongosh --quiet --port {self._port} "
            "--eval \"db.adminCommand('listDatabases')\" "
            "--username admin --password MongoPassword123! --authenticationDatabase admin"
        )        
        code, out = self.exec(cmd)
        log.debug("mongodb_list_dbs_complete", instance=self._instance_id, exit_code=code)
        return out if code == 0 else ""
    
    def create_database(self, db_name: str) -> bool:
        log.info("mongodb_create_db_start", instance=self._instance_id, database=db_name)
        cmd = (
            f"mongosh --quiet --port {self._port} "
            f"--eval \"use {db_name}; db.createCollection('init')\" "
            "--username admin --password MongoPassword123! --authenticationDatabase admin"
        )        
        code, out = self.exec(cmd)
        success = code == 0
        log.info("mongodb_create_db_complete", instance=self._instance_id, database=db_name, success=success)
        return success

@activity.defn
@trace_operation("start_mongodb")
async def start_mongodb_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_mongodb", instance=instance_id)
    
    try:
        manager = MongoDBManager(instance_id=instance_id)
        existing = manager.manager._get_existing_container()
        
        if existing:
            existing.reload()
            if existing.status == "running":
                log.info("container_already_running", service="mongodb", instance=instance_id)
                return True
            
            try:
                existing.start()
                log.info("container_restarted", service="mongodb", instance=instance_id)
                return True
            except Exception:
                existing.remove(force=True)
                log.warning("removed_stale_container", service="mongodb", instance=instance_id)
        
        manager.run()
        log.info("activity_complete", activity="start_mongodb", instance=instance_id)
        return True
    
    except Exception as e:
        log.exception("activity_failed", error=e, activity="start_mongodb", instance=instance_id)
        return False

@activity.defn
@trace_operation("stop_mongodb")
async def stop_mongodb_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_mongodb", instance=instance_id)
    
    try:
        manager = MongoDBManager(instance_id=instance_id)
        manager.stop(timeout=30)
        log.info("activity_complete", activity="stop_mongodb", instance=instance_id)
        return True
    except Exception as e:
        log.exception("activity_failed", error=e, activity="stop_mongodb", instance=instance_id)
        return False

@activity.defn
@trace_operation("restart_mongodb")
async def restart_mongodb_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_mongodb", instance=instance_id)
    
    try:
        manager = MongoDBManager(instance_id=instance_id)
        manager.restart()
        log.info("activity_complete", activity="restart_mongodb", instance=instance_id)
        return True
    except Exception as e:
        log.exception("activity_failed", error=e, activity="restart_mongodb", instance=instance_id)
        return False

@activity.defn
@trace_operation("delete_mongodb")
async def delete_mongodb_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_mongodb", instance=instance_id)
    
    try:
        manager = MongoDBManager(instance_id=instance_id)
        manager.delete(force=False)
        log.info("activity_complete", activity="delete_mongodb", instance=instance_id)
        return True
    except Exception as e:
        log.exception("activity_failed", error=e, activity="delete_mongodb", instance=instance_id)
        return False
