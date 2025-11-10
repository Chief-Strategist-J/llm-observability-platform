import logging
from typing import Dict, Any
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
async def start_kafka_activity(params: Dict[str, Any]) -> bool:
    kafka = KafkaManager()
    kafka.run()
    return True


@activity.defn
async def stop_kafka_activity(params: Dict[str, Any]) -> bool:
    kafka = KafkaManager()
    kafka.stop()
    return True


@activity.defn
async def restart_kafka_activity(params: Dict[str, Any]) -> bool:
    kafka = KafkaManager()
    kafka.restart()
    return True


@activity.defn
async def delete_kafka_activity(params: Dict[str, Any]) -> bool:
    kafka = KafkaManager()
    kafka.delete(force=False)
    return True
