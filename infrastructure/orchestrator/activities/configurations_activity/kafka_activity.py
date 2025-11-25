import logging
from typing import Dict, Any, Optional
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class KafkaManager(BaseService):
    SERVICE_NAME = "Kafka"
    SERVICE_DESCRIPTION = "distributed streaming platform"
    HEALTH_CHECK_TIMEOUT = 60

    def __init__(self, instance_id: int = 0, config: Optional[ContainerConfig] = None) -> None:
        self.instance_id = instance_id
        pm = get_port_manager()

        broker_port = pm.get_port("kafka", instance_id, "broker_port")
        controller_port = pm.get_port("kafka", instance_id, "controller_port")

        logger.info(
            "event=kafka_manager_init instance=%s config_provided=%s broker_port=%s controller_port=%s",
            instance_id, config is not None, broker_port, controller_port
        )

        if config is None:
            container_name = f"kafka-instance-{instance_id}"
            volume_name = f"kafka-data-{instance_id}"

            config = ContainerConfig(
                image="apache/kafka:4.1.1",
                name=container_name,
                ports={
                    broker_port: broker_port,
                    controller_port: controller_port
                },
                volumes={volume_name: "/var/lib/kafka/data"},
                network="data-network",
                memory="1g",
                memory_reservation="512m",
                cpus=1.0,
                restart="unless-stopped",
                user="0:0",
                environment={
                    "CLUSTER_ID": "MkU3OEVBNTcwNTJENDM2Qk",
                    "KAFKA_PROCESS_ROLES": "broker,controller",
                    "KAFKA_NODE_ID": str(instance_id + 1),
                    "KAFKA_LISTENERS": (
                        f"PLAINTEXT://0.0.0.0:{broker_port},"
                        f"CONTROLLER://0.0.0.0:{controller_port}"
                    ),
                    "KAFKA_ADVERTISED_LISTENERS": f"PLAINTEXT://localhost:{broker_port}",
                    "KAFKA_CONTROLLER_QUORUM_VOTERS": (
                        f"{instance_id + 1}@localhost:{controller_port}"
                    ),
                    "KAFKA_CONTROLLER_LISTENER_NAMES": "CONTROLLER",
                    "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": (
                        "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT"
                    ),
                    "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": "1",
                    "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR": "1",
                    "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR": "1",
                    "KAFKA_LOG_DIRS": "/var/lib/kafka/data",
                    "KAFKA_NUM_NETWORK_THREADS": "3",
                    "KAFKA_NUM_IO_THREADS": "8",
                },
                healthcheck={
                    "test": [
                        "CMD-SHELL",
                        f"/opt/kafka/bin/kafka-broker-api-versions.sh "
                        f"--bootstrap-server localhost:{broker_port} || exit 1"
                    ],
                    "interval": 30000000000,
                    "timeout": 10000000000,
                    "retries": 5,
                    "start_period": 60000000000,
                },
            )

            logger.info(
                "event=kafka_manager_config_created instance=%s broker_port=%s controller_port=%s",
                instance_id, broker_port, controller_port
            )

        extra_data = {
            "bootstrap_servers": f"localhost:{broker_port}",
            "broker_host_port": broker_port,
            "controller_host_port": controller_port,
            "instance_id": instance_id
        }

        super().__init__(config=config, extra=extra_data)

        logger.info(
            "event=kafka_manager_initialized instance=%s container=%s image=%s bootstrap=%s broker=%s controller=%s",
            instance_id,
            self.config.name,
            self.config.image,
            extra_data["bootstrap_servers"],
            broker_port,
            controller_port
        )

    def check_broker(self) -> bool:
        broker_port = self.extra.get("broker_host_port")
        cmd = (
            f"/opt/kafka/bin/kafka-broker-api-versions.sh "
            f"--bootstrap-server localhost:{broker_port}"
        )
        code, out = self.exec(cmd)
        result = code == 0

        logger.info(
            "event=kafka_check_broker name=%s success=%s port=%s",
            self.config.name, result, broker_port
        )

        return result

    def list_topics(self) -> str:
        broker_port = self.extra.get("broker_host_port")
        cmd = (
            f"/opt/kafka/bin/kafka-topics.sh "
            f"--bootstrap-server localhost:{broker_port} --list"
        )
        code, out = self.exec(cmd)

        if code == 0:
            logger.info(
                "event=kafka_list_topics_success name=%s port=%s",
                self.config.name, broker_port
            )
            return out

        logger.warning(
            "event=kafka_list_topics_failed name=%s exit_code=%s port=%s",
            self.config.name, code, broker_port
        )
        return ""


@activity.defn
async def start_kafka_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)

    logger.info(
        "event=kafka_start_activity instance=%s params=%s",
        instance_id, list(params.keys())
    )

    try:
        manager = KafkaManager(instance_id=instance_id)
        existing = manager.manager._get_existing_container()

        if existing:
            logger.info(
                "event=kafka_start_existing_detected instance=%s status=%s",
                instance_id, existing.status
            )

            try:
                existing.reload()
            except Exception as err:
                logger.warning(
                    "event=kafka_reload_failed instance=%s error=%s",
                    instance_id, err
                )

            if existing.status == "running":
                logger.info("event=kafka_already_running instance=%s", instance_id)
                return True

            logger.info("event=kafka_start_existing_container instance=%s", instance_id)
            try:
                existing.start()
                return True
            except Exception as err:
                logger.error(
                    "event=kafka_start_existing_failed instance=%s error=%s removing_container=True",
                    instance_id, err
                )
                try:
                    existing.remove(force=True)
                except Exception as rm_err:
                    logger.warning(
                        "event=kafka_remove_failed instance=%s error=%s",
                        instance_id, rm_err
                    )

        logger.info("event=kafka_start_create_new instance=%s", instance_id)
        manager.run()

        logger.info(
            "event=kafka_started instance=%s bootstrap=%s",
            instance_id, manager.extra.get("bootstrap_servers")
        )
        return True

    except Exception as e:
        logger.exception("event=kafka_start_failed instance=%s error=%s", instance_id, e)
        return False


@activity.defn
async def stop_kafka_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)

    logger.info("event=kafka_stop_activity instance=%s", instance_id)

    try:
        manager = KafkaManager(instance_id=instance_id)
        manager.stop(timeout=30)
        logger.info("event=kafka_stopped instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("event=kafka_stop_failed instance=%s error=%s", instance_id, e)
        return False


@activity.defn
async def restart_kafka_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)

    logger.info("event=kafka_restart_activity instance=%s", instance_id)

    try:
        manager = KafkaManager(instance_id=instance_id)
        manager.restart()
        logger.info("event=kafka_restarted instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("event=kafka_restart_failed instance=%s error=%s", instance_id, e)
        return False


@activity.defn
async def delete_kafka_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)

    logger.info("event=kafka_delete_activity instance=%s", instance_id)

    try:
        manager = KafkaManager(instance_id=instance_id)
        manager.delete(force=False)
        logger.info("event=kafka_deleted instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("event=kafka_delete_failed instance=%s error=%s", instance_id, e)
        return False
