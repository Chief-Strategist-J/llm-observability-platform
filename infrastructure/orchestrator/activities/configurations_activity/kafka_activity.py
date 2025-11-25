import logging
from typing import Dict, Any, Optional
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)

class KafkaManager(BaseService):
    SERVICE_NAME = "Kafka"
    SERVICE_DESCRIPTION = "distributed streaming platform"
    DEFAULT_PORT = 9092
    HEALTH_CHECK_TIMEOUT = 60

    def __init__(self, instance_id: int = 0, config: Optional[ContainerConfig] = None) -> None:
        self.instance_id = instance_id
        port_manager = get_port_manager()
        
        broker_host_port = port_manager.get_port("kafka", instance_id, "broker_port")
        controller_host_port = port_manager.get_port("kafka", instance_id, "controller_port")
        
        logger.info("kafka_manager_init_start instance=%s config_provided=%s broker_port=%s controller_port=%s", 
                   instance_id, config is not None, broker_host_port, controller_host_port)
        
        # Initialize ports to None, they will be set either from config or dynamically
        broker_host_port = None
        controller_host_port = None

        logger.info("kafka_manager_init_start instance=%s config_provided=%s", 
                   instance_id, config is not None)
        
        if config is None:
            logger.debug("kafka_manager_creating_default_config instance=%s", instance_id)
            container_name = f"kafka-development-{instance_id}" if instance_id > 0 else "kafka-development"
            volume_name = f"kafka-data-{instance_id}" if instance_id > 0 else "kafka-data"
            
            pm = get_port_manager()
            broker_host_port = pm.get_port("kafka", instance_id, "broker_port")
            controller_host_port = pm.get_port("kafka", instance_id, "controller_port")
            config = ContainerConfig(
                image="apache/kafka:4.1.1",
                name=f"kafka-development-{instance_id}" if instance_id > 0 else "kafka-development",
                ports={9092: broker_host_port, 9093: controller_host_port},
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
                    "KAFKA_NODE_ID": "1",
                    "KAFKA_LISTENERS": "PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093",
                    "KAFKA_ADVERTISED_LISTENERS": f"PLAINTEXT://localhost:{broker_host_port}",
                    "KAFKA_CONTROLLER_QUORUM_VOTERS": "1@localhost:9093",
                    "KAFKA_CONTROLLER_LISTENER_NAMES": "CONTROLLER",
                    "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT",
                    "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": "1",
                    "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR": "1",
                    "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR": "1",
                    "KAFKA_LOG_DIRS": "/var/lib/kafka/data",
                    "KAFKA_NUM_NETWORK_THREADS": "3",
                    "KAFKA_NUM_IO_THREADS": "8",
                },
                healthcheck={
                    "test": ["CMD-SHELL", "/opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 || exit 1"],
                    "interval": 30000000000,
                    "timeout": 10000000000,
                    "retries": 5,
                    "start_period": 60000000000,
                },
            )
            logger.debug("kafka_manager_default_config_created instance=%s container=%s", instance_id, container_name)
        
        host_broker_port = config.ports.get(9092, broker_host_port)
        host_controller_port = config.ports.get(9093, controller_host_port)
        extra_data = {
            "bootstrap_servers": f"localhost:{host_broker_port}", 
            "broker_host_port": int(host_broker_port), 
            "controller_host_port": int(host_controller_port),
            "instance_id": instance_id
        }
        logger.debug("kafka_manager_extra_data_set instance=%s", instance_id)
        super().__init__(config=config, extra=extra_data)
        logger.info("kafka_manager_initialized instance=%s name=%s image=%s bootstrap=%s broker_port=%s controller_port=%s", 
                   instance_id, self.config.name, self.config.image, self.extra.get("bootstrap_servers"), 
                   host_broker_port, host_controller_port)

    def check_broker(self) -> bool:
        cmd = "/opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092"
        code, out = self.exec(cmd)
        result = code == 0
        logger.info("kafka_check_broker_complete name=%s success=%s", self.config.name, result)
        return result

    def list_topics(self) -> str:
        cmd = "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list"
        code, out = self.exec(cmd)
        if code == 0:
            logger.info("kafka_list_topics_success name=%s", self.config.name)
            return out
        logger.warning("kafka_list_topics_failed name=%s exit_code=%s", self.config.name, code)
        return ""

@activity.defn
async def start_kafka_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    logger.info("kafka_start_activity_called instance=%s params_keys=%s", instance_id, list(params.keys()))
    try:
        manager = KafkaManager(instance_id=instance_id)
        existing = manager.manager._get_existing_container()
        if existing:
            logger.info("kafka_start_activity_container_exists instance=%s status=%s", instance_id, existing.status)
            try:
                existing.reload()
            except Exception as reload_err:
                logger.warning("kafka_start_activity_reload_failed instance=%s error=%s", instance_id, reload_err)
            if existing.status == "running":
                logger.info("kafka_start_activity_already_running instance=%s", instance_id)
                return True
            else:
                logger.info("kafka_start_activity_starting_existing_container instance=%s", instance_id)
                try:
                    existing.start()
                    logger.info("kafka_start_activity_started_successfully instance=%s", instance_id)
                    return True
                except Exception as start_err:
                    logger.error("kafka_start_activity_start_failed instance=%s error=%s attempting_recreate=True", instance_id, start_err)
                    try:
                        existing.remove(force=True)
                    except Exception as remove_err:
                        logger.warning("kafka_start_activity_remove_failed instance=%s error=%s", instance_id, remove_err)
        logger.info("kafka_start_activity_creating_new_container instance=%s", instance_id)
        manager.run()
        logger.info("kafka_start_activity_created_and_started instance=%s bootstrap=%s", instance_id, manager.extra.get("bootstrap_servers"))
        return True
    except Exception as e:
        logger.exception("kafka_start_activity_failed instance=%s error=%s", instance_id, e)
        return False

@activity.defn
async def stop_kafka_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    logger.info("kafka_stop_activity_called instance=%s params_keys=%s", instance_id, list(params.keys()))
    try:
        manager = KafkaManager(instance_id=instance_id)
        manager.stop(timeout=30)
        logger.info("kafka_stop_activity_stopped instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("kafka_stop_activity_failed instance=%s error=%s", instance_id, e)
        return False

@activity.defn
async def restart_kafka_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    logger.info("kafka_restart_activity_called instance=%s params_keys=%s", instance_id, list(params.keys()))
    try:
        manager = KafkaManager(instance_id=instance_id)
        manager.restart()
        logger.info("kafka_restart_activity_restarted instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("kafka_restart_activity_failed instance=%s error=%s", instance_id, e)
        return False

@activity.defn
async def delete_kafka_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    logger.info("kafka_delete_activity_called instance=%s params_keys=%s", instance_id, list(params.keys()))
    try:
        manager = KafkaManager(instance_id=instance_id)
        manager.delete(force=False)
        logger.info("kafka_delete_activity_deleted instance=%s", instance_id)
        return True
    except Exception as e:
        logger.exception("kafka_delete_activity_failed instance=%s error=%s", instance_id, e)
        return False
