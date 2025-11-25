import logging
from typing import Dict, Any, Optional
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class KafkaManager(BaseService):
    SERVICE_NAME = "Kafka"
    SERVICE_DESCRIPTION = "distributed streaming platform"
    DEFAULT_PORT = 9092
    HEALTH_CHECK_TIMEOUT = 60

    def __init__(self, config: Optional[ContainerConfig] = None) -> None:
        logger.debug("kafka_manager_init_start config_provided=%s", config is not None)
        
        if config is None:
            logger.debug("kafka_manager_creating_default_config")
            config = ContainerConfig(
                image="apache/kafka:4.0.1",
                name="kafka-development",
                ports={
                    9092: 9092,
                    9093: 9093,
                },
                volumes={
                    "kafka-data": "/var/lib/kafka/data",
                    "kafka-logs": "/opt/kafka/logs",
                },
                network="data-network",
                memory="1g",
                memory_reservation="512m",
                cpus=1.0,
                restart="unless-stopped",
                environment={
                    "KAFKA_PROCESS_ROLES": "broker,controller",
                    "KAFKA_NODE_ID": "1",
                    "KAFKA_LISTENERS": "PLAINTEXT://:9092,CONTROLLER://:9093",
                    "KAFKA_ADVERTISED_LISTENERS": "PLAINTEXT://localhost:9092",
                    "KAFKA_CONTROLLER_QUORUM_VOTERS": "1@localhost:9093",
                    "KAFKA_CONTROLLER_LISTENER_NAMES": "CONTROLLER",
                    "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT",
                    "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": "1",
                    "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR": "1",
                    "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR": "1",
                    "KAFKA_LOG_DIRS": "/var/lib/kafka/data",
                    "KAFKA_LOG_RETENTION_HOURS": "168",
                    "KAFKA_LOG_SEGMENT_BYTES": "1073741824",
                    "KAFKA_LOG_RETENTION_CHECK_INTERVAL_MS": "300000",
                    "KAFKA_NUM_NETWORK_THREADS": "3",
                    "KAFKA_NUM_IO_THREADS": "8",
                    "KAFKA_SOCKET_SEND_BUFFER_BYTES": "102400",
                    "KAFKA_SOCKET_RECEIVE_BUFFER_BYTES": "102400",
                    "KAFKA_SOCKET_REQUEST_MAX_BYTES": "104857600",
                    "CLUSTER_ID": "MkU3OEVBNTcwNTJENDM2Qk",
                },
                healthcheck={
                    "test": [
                        "CMD-SHELL",
                        "/opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 || exit 1"
                    ],
                    "interval": 30000000000,
                    "timeout": 10000000000,
                    "retries": 5,
                    "start_period": 60000000000
                }
            )
            logger.debug("kafka_manager_default_config_created")
        
        extra_data = {
            "bootstrap_servers": "localhost:9092",
            "cluster_id": "MkU3OEVBNTcwNTJENDM2Qk"
        }
        logger.debug("kafka_manager_extra_data_set")
        
        super().__init__(config=config, extra=extra_data)
        logger.info("kafka_manager_initialized name=%s image=%s", self.config.name, self.config.image)

    def check_broker(self) -> bool:
        logger.debug("kafka_check_broker_start name=%s", self.config.name)
        try:
            cmd = "/opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092"
            logger.debug("kafka_check_broker_executing name=%s", self.config.name)
            
            code, out = self.exec(cmd)
            
            logger.debug("kafka_check_broker_result name=%s exit_code=%s output_length=%s",
                        self.config.name, code, len(out) if out else 0)
            
            result = code == 0
            logger.info("kafka_check_broker_complete name=%s success=%s", self.config.name, result)
            return result
            
        except Exception as e:
            logger.exception("kafka_check_broker_error name=%s error=%s", self.config.name, e)
            return False

    def list_topics(self) -> str:
        logger.debug("kafka_list_topics_start name=%s", self.config.name)
        try:
            cmd = "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list"
            logger.debug("kafka_list_topics_executing name=%s", self.config.name)
            
            code, out = self.exec(cmd)
            
            logger.debug("kafka_list_topics_result name=%s exit_code=%s output_length=%s",
                        self.config.name, code, len(out) if out else 0)
            
            if code == 0:
                logger.info("kafka_list_topics_success name=%s", self.config.name)
                return out
            else:
                logger.warning("kafka_list_topics_failed name=%s exit_code=%s", self.config.name, code)
                return ""
                
        except Exception as e:
            logger.exception("kafka_list_topics_error name=%s error=%s", self.config.name, e)
            return ""

    def create_topic(self, topic_name: str, partitions: int = 1, replication_factor: int = 1) -> bool:
        logger.debug("kafka_create_topic_start name=%s topic=%s partitions=%s replication=%s",
                    self.config.name, topic_name, partitions, replication_factor)
        try:
            cmd = f"/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic {topic_name} --partitions {partitions} --replication-factor {replication_factor}"
            logger.debug("kafka_create_topic_executing name=%s topic=%s", self.config.name, topic_name)
            
            code, out = self.exec(cmd)
            
            logger.debug("kafka_create_topic_result name=%s topic=%s exit_code=%s",
                        self.config.name, topic_name, code)
            
            result = code == 0
            if result:
                logger.info("kafka_create_topic_success name=%s topic=%s", self.config.name, topic_name)
            else:
                logger.warning("kafka_create_topic_failed name=%s topic=%s exit_code=%s output=%s",
                             self.config.name, topic_name, code, out)
            
            return result
            
        except Exception as e:
            logger.exception("kafka_create_topic_error name=%s topic=%s error=%s",
                           self.config.name, topic_name, e)
            return False

    def describe_topic(self, topic_name: str) -> str:
        logger.debug("kafka_describe_topic_start name=%s topic=%s", self.config.name, topic_name)
        try:
            cmd = f"/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic {topic_name}"
            logger.debug("kafka_describe_topic_executing name=%s topic=%s", self.config.name, topic_name)
            
            code, out = self.exec(cmd)
            
            logger.debug("kafka_describe_topic_result name=%s topic=%s exit_code=%s output_length=%s",
                        self.config.name, topic_name, code, len(out) if out else 0)
            
            if code == 0:
                logger.info("kafka_describe_topic_success name=%s topic=%s", self.config.name, topic_name)
                return out
            else:
                logger.warning("kafka_describe_topic_failed name=%s topic=%s exit_code=%s",
                             self.config.name, topic_name, code)
                return ""
                
        except Exception as e:
            logger.exception("kafka_describe_topic_error name=%s topic=%s error=%s",
                           self.config.name, topic_name, e)
            return ""


@activity.defn
async def start_kafka_activity(params: Dict[str, Any]) -> bool:
    logger.info("kafka_start_activity_called params_keys=%s", list(params.keys()))
    try:
        logger.debug("kafka_start_activity_creating_manager")
        manager = KafkaManager()
        
        logger.debug("kafka_start_activity_checking_existing")
        existing = manager.manager._get_existing_container()
        
        if existing:
            logger.info("kafka_start_activity_container_exists status=%s", existing.status)
            try:
                existing.reload()
                logger.debug("kafka_start_activity_container_reloaded status=%s", existing.status)
            except Exception as reload_err:
                logger.warning("kafka_start_activity_reload_failed error=%s", reload_err)
            
            if existing.status == "running":
                logger.info("kafka_start_activity_already_running")
                return True
            else:
                logger.info("kafka_start_activity_starting_existing_container")
                try:
                    existing.start()
                    logger.info("kafka_start_activity_started_successfully")
                    return True
                except Exception as start_err:
                    logger.error("kafka_start_activity_start_failed error=%s attempting_recreate=True",
                               start_err)
                    try:
                        logger.debug("kafka_start_activity_removing_failed_container")
                        existing.remove(force=True)
                        logger.debug("kafka_start_activity_failed_container_removed")
                    except Exception as remove_err:
                        logger.warning("kafka_start_activity_remove_failed error=%s", remove_err)
        
        logger.info("kafka_start_activity_creating_new_container")
        manager.run()
        logger.info("kafka_start_activity_created_and_started")
        return True
        
    except Exception as e:
        logger.exception("kafka_start_activity_failed error=%s", e)
        return False


@activity.defn
async def stop_kafka_activity(params: Dict[str, Any]) -> bool:
    logger.info("kafka_stop_activity_called params_keys=%s", list(params.keys()))
    try:
        logger.debug("kafka_stop_activity_creating_manager")
        manager = KafkaManager()
        
        logger.info("kafka_stop_activity_stopping timeout=30")
        manager.stop(timeout=30)
        
        logger.info("kafka_stop_activity_stopped")
        return True
        
    except Exception as e:
        logger.exception("kafka_stop_activity_failed error=%s", e)
        return False


@activity.defn
async def restart_kafka_activity(params: Dict[str, Any]) -> bool:
    logger.info("kafka_restart_activity_called params_keys=%s", list(params.keys()))
    try:
        logger.debug("kafka_restart_activity_creating_manager")
        manager = KafkaManager()
        
        logger.info("kafka_restart_activity_restarting")
        manager.restart()
        
        logger.info("kafka_restart_activity_restarted")
        return True
        
    except Exception as e:
        logger.exception("kafka_restart_activity_failed error=%s", e)
        return False


@activity.defn
async def delete_kafka_activity(params: Dict[str, Any]) -> bool:
    logger.info("kafka_delete_activity_called params_keys=%s", list(params.keys()))
    try:
        logger.debug("kafka_delete_activity_creating_manager")
        manager = KafkaManager()
        
        logger.info("kafka_delete_activity_deleting force=False")
        manager.delete(force=False)
        
        logger.info("kafka_delete_activity_deleted")
        return True
        
    except Exception as e:
        logger.exception("kafka_delete_activity_failed error=%s", e)
        return False