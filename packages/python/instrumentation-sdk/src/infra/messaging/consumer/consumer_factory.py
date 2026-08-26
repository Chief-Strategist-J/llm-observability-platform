import json
from typing import Optional
from kafka import KafkaConsumer
from ..broker.broker_config import KafkaBrokerConfig, kafka_broker_config

class KafkaConsumerFactory:
    def __init__(self, config: Optional[KafkaBrokerConfig] = None):
        self.config = config or kafka_broker_config

    def create_consumer(self, topic: str, group_id: str) -> KafkaConsumer:
        kwargs = {
            "bootstrap_servers": self.config.bootstrap_servers,
            "group_id": group_id,
            "auto_offset_reset": "earliest",
            "enable_auto_commit": False,
            "security_protocol": self.config.security_protocol,
            "value_deserializer": lambda m: json.loads(m.decode("utf-8")),
        }
        if self.config.sasl_mechanism:
            kwargs["sasl_mechanism"] = self.config.sasl_mechanism
            kwargs["sasl_plain_username"] = self.config.sasl_plain_username
            kwargs["sasl_plain_password"] = self.config.sasl_plain_password

        return KafkaConsumer(topic, **kwargs)

kafka_consumer_factory = KafkaConsumerFactory()
