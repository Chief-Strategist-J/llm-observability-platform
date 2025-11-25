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
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0, config: Optional[ContainerConfig] = None) -> None:
        self.instance_id = instance_id
        pm = get_port_manager()

        ui_port = pm.get_port("mongo_express", instance_id, "port")

        logger.info(
            "event=mongoexpress_manager_init instance=%s config_provided=%s ui_port=%s",
            instance_id, config is not None, ui_port
        )

        if config is None:
            container_name = f"mongo-express-{instance_id}"

            config = ContainerConfig(
                image="mongo-express:latest",
                name=container_name,
                ports={ui_port: ui_port},
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
                    "ME_CONFIG_SITE_PORT": str(ui_port),
                },
                healthcheck={
                    "test": [
                        "CMD-SHELL",
                        f"curl -sSf http://localhost:{ui_port}/ || exit 1"
                    ],
                    "interval": 30000000000,
                    "timeout": 10000000000,
                    "retries": 5,
                    "start_period": 20000000000,
                },
            )

            logger.info(
                "event=mongoexpress_manager_default_config_created instance=%s container=%s",
                instance_id, container_name
            )

        extra_data = {"ui_host_port": ui_port, "instance_id": instance_id}

        logger.info("event=mongoexpress_manager_extra_data_set instance=%s ui_port=%s", instance_id, ui_port)

        super().__init__(config=config, extra=extra_data)

        logger.info(
            "event=mongoexpress_manager_initialized instance=%s container=%s image=%s ui_port=%s",
            instance_id, self.config.name, self.config.image, ui_port
        )

    def get_ui_url(self) -> str:
        port = self.extra.get("ui_host_port")
        return f"http://localhost:{port}"


@activity.defn
async def start_mongoexpress_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)

    logger.info(
        "event=mongoexpress_start_activity instance=%s keys=%s",
        instance_id, list(params.keys())
    )

    try:
        manager = MongoExpressManager(instance_id=instance_id)
        existing = manager.manager._get_existing_container()

        if existing:
            logger.info(
                "event=mongoexpress_container_exists instance=%s status=%s",
                instance_id, existing.status
            )

            try:
                existing.reload()
            except Exception as err:
                logger.warning(
                    "event=mongoexpress_reload_failed instance=%s error=%s",
                    instance_id, err
                )

            if existing.status == "running":
                logger.info(
                    "event=mongoexpress_already_running instance=%s url=%s",
                    instance_id, manager.get_ui_url()
                )
                return True

            try:
                existing.start()
                logger.info(
                    "event=mongoexpress_existing_started instance=%s url=%s",
                    instance_id, manager.get_ui_url()
                )
                return True
            except Exception as err:
                logger.error(
                    "event=mongoexpress_start_existing_failed instance=%s error=%s removing_container=True",
                    instance_id, err
                )
                try:
                    existing.remove(force=True)
                except Exception as rm_err:
                    logger.warning(
                        "event=mongoexpress_remove_failed instance=%s error=%s",
                        instance_id, rm_err
                    )

        logger.info("event=mongoexpress_creating_new_container instance=%s", instance_id)
        manager.run()

        logger.info(
            "event=mongoexpress_started instance=%s url=%s",
            instance_id, manager.get_ui_url()
        )

        return True

    except Exception as e:
        logger.exception("event=mongoexpress_start_failed instance=%s error=%s", instance_id, e)
        return False


@activity.defn
async def stop_mongoexpress_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)

    logger.info("event=mongoexpress_stop_activity instance=%s", instance_id)

    try:
        manager = MongoExpressManager(instance_id=instance_id)
        manager.stop(timeout=30)

        logger.info("event=mongoexpress_stopped instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("event=mongoexpress_stop_failed instance=%s error=%s", instance_id, e)
        return False


@activity.defn
async def restart_mongoexpress_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)

    logger.info("event=mongoexpress_restart_activity instance=%s", instance_id)

    try:
        manager = MongoExpressManager(instance_id=instance_id)
        manager.restart()
        logger.info("event=mongoexpress_restarted instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("event=mongoexpress_restart_failed instance=%s error=%s", instance_id, e)
        return False


@activity.defn
async def delete_mongoexpress_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)

    logger.info("event=mongoexpress_delete_activity instance=%s", instance_id)

    try:
        manager = MongoExpressManager(instance_id=instance_id)
        manager.delete(force=False)
        logger.info("event=mongoexpress_deleted instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("event=mongoexpress_delete_failed instance=%s error=%s", instance_id, e)
        return False
