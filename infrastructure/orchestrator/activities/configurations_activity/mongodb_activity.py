import logging
from typing import Dict, Any, Optional
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class MongoDBManager(BaseService):
    SERVICE_NAME = "MongoDB"
    SERVICE_DESCRIPTION = "document database"
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0, config: Optional[ContainerConfig] = None) -> None:
        pm = get_port_manager()
        mongo_port = pm.get_port("mongodb", instance_id, "port")

        logger.info(
            "event=mongodb_manager_init instance=%s config_provided=%s port=%s",
            instance_id, config is not None, mongo_port
        )

        if config is None:
            container_name = f"mongodb-instance-{instance_id}"
            volume_data = f"mongodb-data-{instance_id}"
            volume_cfg = f"mongodb-config-{instance_id}"

            config = ContainerConfig(
                image="mongo:8.0",
                name=container_name,
                ports={mongo_port: mongo_port},
                volumes={
                    volume_data: "/data/db",
                    volume_cfg: "/data/configdb"
                },
                network="data-network",
                memory="1g",
                memory_reservation="512m",
                cpus=1.0,
                restart="unless-stopped",
                environment={
                    "MONGO_INITDB_ROOT_USERNAME": "admin",
                    "MONGO_INITDB_ROOT_PASSWORD": "MongoPassword123!",
                    "MONGO_INITDB_DATABASE": "admin"
                },
                command=[
                    "mongod",
                    "--auth",
                    "--bind_ip_all",
                    "--wiredTigerCacheSizeGB", "0.5"
                ],
                healthcheck={
                    "test": [
                        "CMD-SHELL",
                        f"mongosh --quiet --port {mongo_port} "
                        "--eval \"db.adminCommand('ping')\" --username admin "
                        "--password MongoPassword123! --authenticationDatabase admin || exit 1"
                    ],
                    "interval": 30000000000,
                    "timeout": 10000000000,
                    "retries": 3,
                    "start_period": 40000000000
                }
            )

        extra_data = {
            "port": mongo_port,
            "username": "admin",
            "password": "MongoPassword123!",
            "auth_database": "admin",
            "instance_id": instance_id
        }

        super().__init__(config=config, extra=extra_data)

        logger.info(
            "event=mongodb_manager_initialized instance=%s name=%s port=%s",
            instance_id, self.config.name, mongo_port
        )

    def ping(self) -> bool:
        port = self.extra["port"]
        cmd = (
            f"mongosh --quiet --port {port} --eval \"db.adminCommand('ping')\" "
            "--username admin --password MongoPassword123! --authenticationDatabase admin"
        )
        code, out = self.exec(cmd)
        result = code == 0 and out and "ok" in out.lower()

        logger.info(
            "event=mongodb_ping instance=%s success=%s port=%s",
            self.extra["instance_id"], result, port
        )

        return result

    def get_server_status(self) -> str:
        port = self.extra["port"]
        cmd = (
            f"mongosh --quiet --port {port} "
            "--eval \"JSON.stringify(db.serverStatus())\" "
            "--username admin --password MongoPassword123! --authenticationDatabase admin"
        )

        code, out = self.exec(cmd)
        if code == 0:
            logger.info(
                "event=mongodb_server_status_success instance=%s port=%s",
                self.extra["instance_id"], port
            )
            return out

        logger.warning(
            "event=mongodb_server_status_failed instance=%s exit_code=%s port=%s",
            self.extra["instance_id"], code, port
        )
        return ""

    def list_databases(self) -> str:
        port = self.extra["port"]
        cmd = (
            f"mongosh --quiet --port {port} "
            "--eval \"db.adminCommand('listDatabases')\" "
            "--username admin --password MongoPassword123! --authenticationDatabase admin"
        )

        code, out = self.exec(cmd)
        if code == 0:
            logger.info(
                "event=mongodb_list_databases_success instance=%s port=%s",
                self.extra["instance_id"], port
            )
            return out

        logger.warning(
            "event=mongodb_list_databases_failed instance=%s exit_code=%s port=%s",
            self.extra["instance_id"], code, port
        )
        return ""

    def create_database(self, db_name: str) -> bool:
        port = self.extra["port"]
        cmd = (
            f"mongosh --quiet --port {port} "
            f"--eval \"use {db_name}; db.createCollection('init')\" "
            "--username admin --password MongoPassword123! --authenticationDatabase admin"
        )

        code, out = self.exec(cmd)
        success = code == 0

        logger.info(
            "event=mongodb_create_database instance=%s db=%s success=%s port=%s",
            self.extra["instance_id"], db_name, success, port
        )

        return success


@activity.defn
async def start_mongodb_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    logger.info("event=mongodb_start_activity instance=%s", instance_id)

    try:
        manager = MongoDBManager(instance_id=instance_id)
        existing = manager.manager._get_existing_container()

        if existing:
            existing.reload()
            if existing.status == "running":
                logger.info("event=mongodb_already_running instance=%s", instance_id)
                return True

            try:
                existing.start()
                logger.info("event=mongodb_existing_started instance=%s", instance_id)
                return True
            except Exception:
                existing.remove(force=True)

        manager.run()
        logger.info("event=mongodb_started instance=%s", instance_id)
        return True

    except Exception as e:
        logger.exception("event=mongodb_start_failed instance=%s error=%s", instance_id, e)
        return False


@activity.defn
async def stop_mongodb_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    logger.info("event=mongodb_stop_activity instance=%s", instance_id)

    try:
        manager = MongoDBManager(instance_id=instance_id)
        manager.stop(timeout=30)
        logger.info("event=mongodb_stopped instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("event=mongodb_stop_failed instance=%s error=%s", instance_id, e)
        return False


@activity.defn
async def restart_mongodb_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    logger.info("event=mongodb_restart_activity instance=%s", instance_id)

    try:
        manager = MongoDBManager(instance_id=instance_id)
        manager.restart()
        logger.info("event=mongodb_restarted instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("event=mongodb_restart_failed instance=%s error=%s", instance_id, e)
        return False


@activity.defn
async def delete_mongodb_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    logger.info("event=mongodb_delete_activity instance=%s", instance_id)

    try:
        manager = MongoDBManager(instance_id=instance_id)
        manager.delete(force=False)
        logger.info("event=mongodb_deleted instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("event=mongodb_delete_failed instance=%s error=%s", instance_id, e)
        return False
