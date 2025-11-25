import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
from typing import Dict, Any, Optional
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class MongoExpressManager(BaseService):
    SERVICE_NAME = "MongoExpress"
    SERVICE_DESCRIPTION = "MongoDB web admin UI"
    DEFAULT_PORT = 8081
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0, config: Optional[ContainerConfig] = None) -> None:
        self.instance_id = instance_id
        port_manager = get_port_manager()
        
        ui_host_port = port_manager.get_port("mongo_express", instance_id, "port")
        
        logger.info("mongoexpress_manager_init_start instance=%s config_provided=%s ui_port=%s", 
                   instance_id, config is not None, ui_host_port)
        
        if config is None:
            logger.debug("mongoexpress_manager_creating_default_config instance=%s", instance_id)
            container_name = f"mongo-express-ui-{instance_id}" if instance_id > 0 else "mongo-express-ui"
            
            config = ContainerConfig(
                image="mongo-express:latest",
                name=container_name,
                ports={8081: ui_host_port},
                network="data-network",
                memory="512m",
                memory_reservation="256m",
                cpus=0.5,
                restart="unless-stopped",
                environment={
                    "ME_CONFIG_MONGODB_SERVER": "mongodb-development",
                    "ME_CONFIG_MONGODB_ADMINUSERNAME": "admin",
                    "ME_CONFIG_MONGODB_ADMINPASSWORD": "MongoPassword123!",
                    "ME_CONFIG_BASICAUTH_USERNAME": "admin",
                    "ME_CONFIG_BASICAUTH_PASSWORD": "AdminPassword!",
                    "ME_CONFIG_SITE_BASEURL": "/",
                    "ME_CONFIG_SITE_PORT": "8081",
                },
                healthcheck={
                    "test": ["CMD-SHELL", "curl -sSf http://localhost:8081/ || exit 1"],
                    "interval": 30000000000,
                    "timeout": 10000000000,
                    "retries": 5,
                    "start_period": 20000000000,
                },
            )
            logger.debug("mongoexpress_manager_default_config_created instance=%s container=%s", instance_id, container_name)
        
        extra_data = {"ui_host_port": int(ui_host_port), "instance_id": instance_id}
        logger.debug("mongoexpress_manager_extra_data_set instance=%s", instance_id)
        super().__init__(config=config, extra=extra_data)
        logger.info("mongoexpress_manager_initialized instance=%s name=%s image=%s ui_port=%s", 
                   instance_id, self.config.name, self.config.image, self.extra.get("ui_host_port"))

    def get_ui_url(self) -> str:
        port = int(self.extra.get("ui_host_port", 0))
        return f"http://localhost:{port}"

@activity.defn
async def start_mongoexpress_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    logger.info("mongoexpress_start_activity_called instance=%s params_keys=%s", instance_id, list(params.keys()))
    try:
        manager = MongoExpressManager(instance_id=instance_id)
        existing = manager.manager._get_existing_container()
        if existing:
            logger.info("mongoexpress_start_activity_container_exists instance=%s status=%s", instance_id, existing.status)
            try:
                existing.reload()
            except Exception as reload_err:
                logger.warning("mongoexpress_start_activity_reload_failed instance=%s error=%s", instance_id, reload_err)
            if existing.status == "running":
                logger.info("mongoexpress_start_activity_already_running instance=%s ui=%s", instance_id, manager.get_ui_url())
                return True
            else:
                try:
                    existing.start()
                    logger.info("mongoexpress_start_activity_started_successfully instance=%s ui=%s", instance_id, manager.get_ui_url())
                    return True
                except Exception as start_err:
                    logger.error("mongoexpress_start_activity_start_failed instance=%s error=%s attempting_recreate=True", instance_id, start_err)
                    try:
                        existing.remove(force=True)
                    except Exception as remove_err:
                        logger.warning("mongoexpress_start_activity_remove_failed instance=%s error=%s", instance_id, remove_err)
        logger.info("mongoexpress_start_activity_creating_new_container instance=%s", instance_id)
        manager.run()
        logger.info("mongoexpress_start_activity_created_and_started instance=%s ui=%s", instance_id, manager.get_ui_url())
        return True
    except Exception as e:
        logger.exception("mongoexpress_start_activity_failed instance=%s error=%s", instance_id, e)
        return False

@activity.defn
async def stop_mongoexpress_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    logger.info("mongoexpress_stop_activity_called instance=%s params_keys=%s", instance_id, list(params.keys()))
    try:
        manager = MongoExpressManager(instance_id=instance_id)
        manager.stop(timeout=30)
        logger.info("mongoexpress_stop_activity_stopped instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("mongoexpress_stop_activity_failed instance=%s error=%s", instance_id, e)
        return False

@activity.defn
async def restart_mongoexpress_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    logger.info("mongoexpress_restart_activity_called instance=%s params_keys=%s", instance_id, list(params.keys()))
    try:
        manager = MongoExpressManager(instance_id=instance_id)
        manager.restart()
        logger.info("mongoexpress_restart_activity_restarted instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("mongoexpress_restart_activity_failed instance=%s error=%s", instance_id, e)
        return False

@activity.defn
async def delete_mongoexpress_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    logger.info("mongoexpress_delete_activity_called instance=%s params_keys=%s", instance_id, list(params.keys()))
    try:
        manager = MongoExpressManager(instance_id=instance_id)
        manager.delete(force=False)
        logger.info("mongoexpress_delete_activity_deleted instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("mongoexpress_delete_activity_failed instance=%s error=%s", instance_id, e)
        return False
