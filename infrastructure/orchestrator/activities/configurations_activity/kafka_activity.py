import logging
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)

class KafkaManager(BaseService):
    SERVICE_NAME = "Kafka"

    def __init__(self):
        config = ContainerConfig(
            image="apache/kafka:4.0.1",
            name="kafka-development",
            ports={9092: 9092},
            volumes={"kafka-data": "/var/lib/kafka/data"},
            network="monitoring-bridge",
            environment={
                "KAFKA_PROCESS_ROLES": "broker,controller",
                "KAFKA_NODE_ID": "1",
                "KAFKA_LISTENERS": "PLAINTEXT://:9092,CONTROLLER://:9093",
                "KAFKA_ADVERTISED_LISTENERS": "PLAINTEXT://localhost:9092",
                "KAFKA_CONTROLLER_QUORUM_VOTERS": "1@localhost:9093",
                "ALLOW_PLAINTEXT_LISTENER": "yes",
            },
        )
        super().__init__(config)
        logger.info("KafkaManager initialized")

@activity.defn
async def start_kafka_activity(service_name: str) -> bool:
    try:
        kafka = KafkaManager()
        kafka.run()
        return True
    except Exception as e:
        logger.error("Failed to start Kafka service %s: %s", service_name, e, exc_info=True)
        raise Exception(f"Kafka start failed: {e}") from e

@activity.defn
async def stop_kafka_activity(service_name: str) -> bool:
    try:
        kafka = KafkaManager()
        kafka.stop()
        return True
    except Exception as e:
        logger.error("Failed to stop Kafka service %s: %s", service_name, e, exc_info=True)
        raise Exception(f"Kafka stop failed: {e}") from e

@activity.defn
async def restart_kafka_activity(service_name: str) -> bool:
    try:
        kafka = KafkaManager()
        kafka.restart()
        return True
    except Exception as e:
        logger.error("Failed to restart Kafka service %s: %s", service_name, e, exc_info=True)
        raise Exception(f"Kafka restart failed: {e}") from e

@activity.defn
async def delete_kafka_activity(service_name: str, force: bool = False) -> bool:
    try:
        kafka = KafkaManager()
        kafka.delete(force=force)
        return True
    except Exception as e:
        logger.error("Failed to delete Kafka service %s: %s", service_name, e, exc_info=True)
        raise Exception(f"Kafka delete failed: {e}") from e
