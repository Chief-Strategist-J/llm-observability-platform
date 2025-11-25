import logging
from typing import Dict, Any, Optional
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class MongoDBManager(BaseService):
    SERVICE_NAME = "MongoDB"
    SERVICE_DESCRIPTION = "document database"
    DEFAULT_PORT = 27017
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, config: Optional[ContainerConfig] = None) -> None:
        logger.debug("mongodb_manager_init_start config_provided=%s", config is not None)
        
        if config is None:
            logger.debug("mongodb_manager_creating_default_config")
            config = ContainerConfig(
                image="mongo:8.0",
                name="mongodb-development",
                ports={27017: 27017},
                volumes={
                    "mongodb-data": "/data/db",
                    "mongodb-config": "/data/configdb",
                },
                network="data-network",
                memory="1g",
                memory_reservation="512m",
                cpus=1.0,
                restart="unless-stopped",
                environment={
                    "MONGO_INITDB_ROOT_USERNAME": "admin",
                    "MONGO_INITDB_ROOT_PASSWORD": "MongoPassword123!",
                    "MONGO_INITDB_DATABASE": "admin",
                },
                command=[
                    "mongod",
                    "--auth",
                    "--bind_ip_all",
                    "--wiredTigerCacheSizeGB", "0.5",
                ],
                healthcheck={
                    "test": [
                        "CMD",
                        "mongosh",
                        "--quiet",
                        "--eval",
                        "db.adminCommand('ping')"
                    ],
                    "interval": 30000000000,
                    "timeout": 10000000000,
                    "retries": 3,
                    "start_period": 40000000000
                }
            )
            logger.debug("mongodb_manager_default_config_created")
        
        extra_data = {
            "username": "admin",
            "password": "MongoPassword123!",
            "auth_database": "admin"
        }
        logger.debug("mongodb_manager_extra_data_set")
        
        super().__init__(config=config, extra=extra_data)
        logger.info("mongodb_manager_initialized name=%s image=%s", self.config.name, self.config.image)

    def ping(self) -> bool:
        logger.debug("mongodb_ping_start name=%s", self.config.name)
        try:
            cmd = 'mongosh --quiet --eval "db.adminCommand(\'ping\')" --username admin --password MongoPassword123! --authenticationDatabase admin'
            logger.debug("mongodb_ping_executing_cmd name=%s", self.config.name)
            
            code, out = self.exec(cmd)
            
            logger.debug("mongodb_ping_result name=%s exit_code=%s output_length=%s", 
                        self.config.name, code, len(out) if out else 0)
            
            result = code == 0 and "ok" in out.lower()
            logger.info("mongodb_ping_complete name=%s success=%s", self.config.name, result)
            return result
            
        except Exception as e:
            logger.exception("mongodb_ping_error name=%s error=%s", self.config.name, e)
            return False

    def get_server_status(self) -> str:
        logger.debug("mongodb_server_status_start name=%s", self.config.name)
        try:
            cmd = 'mongosh --quiet --eval "JSON.stringify(db.serverStatus())" --username admin --password MongoPassword123! --authenticationDatabase admin'
            logger.debug("mongodb_server_status_executing name=%s", self.config.name)
            
            code, out = self.exec(cmd)
            
            logger.debug("mongodb_server_status_result name=%s exit_code=%s output_length=%s",
                        self.config.name, code, len(out) if out else 0)
            
            if code == 0:
                logger.info("mongodb_server_status_success name=%s", self.config.name)
                return out
            else:
                logger.warning("mongodb_server_status_failed name=%s exit_code=%s", 
                             self.config.name, code)
                return ""
                
        except Exception as e:
            logger.exception("mongodb_server_status_error name=%s error=%s", self.config.name, e)
            return ""

    def list_databases(self) -> str:
        logger.debug("mongodb_list_databases_start name=%s", self.config.name)
        try:
            cmd = 'mongosh --quiet --eval "db.adminCommand(\'listDatabases\')" --username admin --password MongoPassword123! --authenticationDatabase admin'
            logger.debug("mongodb_list_databases_executing name=%s", self.config.name)
            
            code, out = self.exec(cmd)
            
            logger.debug("mongodb_list_databases_result name=%s exit_code=%s output_length=%s",
                        self.config.name, code, len(out) if out else 0)
            
            if code == 0:
                logger.info("mongodb_list_databases_success name=%s", self.config.name)
                return out
            else:
                logger.warning("mongodb_list_databases_failed name=%s exit_code=%s",
                             self.config.name, code)
                return ""
                
        except Exception as e:
            logger.exception("mongodb_list_databases_error name=%s error=%s", self.config.name, e)
            return ""

    def create_database(self, db_name: str) -> bool:
        logger.debug("mongodb_create_database_start name=%s db_name=%s", self.config.name, db_name)
        try:
            cmd = f'mongosh --quiet --eval "use {db_name}; db.createCollection(\'init\')" --username admin --password MongoPassword123! --authenticationDatabase admin'
            logger.debug("mongodb_create_database_executing name=%s db_name=%s", self.config.name, db_name)
            
            code, out = self.exec(cmd)
            
            logger.debug("mongodb_create_database_result name=%s db_name=%s exit_code=%s",
                        self.config.name, db_name, code)
            
            result = code == 0
            if result:
                logger.info("mongodb_create_database_success name=%s db_name=%s", 
                           self.config.name, db_name)
            else:
                logger.warning("mongodb_create_database_failed name=%s db_name=%s exit_code=%s",
                             self.config.name, db_name, code)
            
            return result
            
        except Exception as e:
            logger.exception("mongodb_create_database_error name=%s db_name=%s error=%s",
                           self.config.name, db_name, e)
            return False


@activity.defn
async def start_mongodb_activity(params: Dict[str, Any]) -> bool:
    logger.info("mongodb_start_activity_called params_keys=%s", list(params.keys()))
    try:
        logger.debug("mongodb_start_activity_creating_manager")
        manager = MongoDBManager()
        
        logger.debug("mongodb_start_activity_checking_existing")
        existing = manager.manager._get_existing_container()
        
        if existing:
            logger.info("mongodb_start_activity_container_exists status=%s", existing.status)
            try:
                existing.reload()
                logger.debug("mongodb_start_activity_container_reloaded status=%s", existing.status)
            except Exception as reload_err:
                logger.warning("mongodb_start_activity_reload_failed error=%s", reload_err)
            
            if existing.status == "running":
                logger.info("mongodb_start_activity_already_running")
                return True
            else:
                logger.info("mongodb_start_activity_starting_existing_container")
                try:
                    existing.start()
                    logger.info("mongodb_start_activity_started_successfully")
                    return True
                except Exception as start_err:
                    logger.error("mongodb_start_activity_start_failed error=%s attempting_recreate=True", 
                               start_err)
                    try:
                        logger.debug("mongodb_start_activity_removing_failed_container")
                        existing.remove(force=True)
                        logger.debug("mongodb_start_activity_failed_container_removed")
                    except Exception as remove_err:
                        logger.warning("mongodb_start_activity_remove_failed error=%s", remove_err)
        
        logger.info("mongodb_start_activity_creating_new_container")
        manager.run()
        logger.info("mongodb_start_activity_created_and_started")
        return True
        
    except Exception as e:
        logger.exception("mongodb_start_activity_failed error=%s", e)
        return False


@activity.defn
async def stop_mongodb_activity(params: Dict[str, Any]) -> bool:
    logger.info("mongodb_stop_activity_called params_keys=%s", list(params.keys()))
    try:
        logger.debug("mongodb_stop_activity_creating_manager")
        manager = MongoDBManager()
        
        logger.info("mongodb_stop_activity_stopping timeout=30")
        manager.stop(timeout=30)
        
        logger.info("mongodb_stop_activity_stopped")
        return True
        
    except Exception as e:
        logger.exception("mongodb_stop_activity_failed error=%s", e)
        return False


@activity.defn
async def restart_mongodb_activity(params: Dict[str, Any]) -> bool:
    logger.info("mongodb_restart_activity_called params_keys=%s", list(params.keys()))
    try:
        logger.debug("mongodb_restart_activity_creating_manager")
        manager = MongoDBManager()
        
        logger.info("mongodb_restart_activity_restarting")
        manager.restart()
        
        logger.info("mongodb_restart_activity_restarted")
        return True
        
    except Exception as e:
        logger.exception("mongodb_restart_activity_failed error=%s", e)
        return False


@activity.defn
async def delete_mongodb_activity(params: Dict[str, Any]) -> bool:
    logger.info("mongodb_delete_activity_called params_keys=%s", list(params.keys()))
    try:
        logger.debug("mongodb_delete_activity_creating_manager")
        manager = MongoDBManager()
        
        logger.info("mongodb_delete_activity_deleting force=False")
        manager.delete(force=False)
        
        logger.info("mongodb_delete_activity_deleted")
        return True
        
    except Exception as e:
        logger.exception("mongodb_delete_activity_failed error=%s", e)
        return False