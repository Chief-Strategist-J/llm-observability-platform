import json
import threading
from typing import Optional
try:
    from kafka import KafkaProducer
except ImportError:
    try:
        from confluent_kafka import Producer as KafkaProducer
    except ImportError:
        KafkaProducer = None

from src.infra.messaging.broker.broker_config import KafkaBrokerConfig, kafka_broker_config

class KafkaProducerFactory:
    _instance: Optional["KafkaProducerFactory"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, config: Optional[KafkaBrokerConfig] = None):
        self.config = config or kafka_broker_config
        self._producer: Optional[KafkaProducer] = None

    @classmethod
    def get_instance(cls, config: Optional[KafkaBrokerConfig] = None) -> "KafkaProducerFactory":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    def get_producer(self) -> KafkaProducer:
        if self._producer is None:
            with self._lock:
                if self._producer is None:
                    kwargs = {
                        "bootstrap_servers": self.config.bootstrap_servers,
                        "client_id": self.config.client_id,
                        "acks": self.config.acks,
                        "retries": self.config.retries,
                        "max_in_flight_requests_per_connection": self.config.max_in_flight_requests_per_connection,
                        "compression_type": self.config.compression_type,
                        "batch_size": self.config.batch_size,
                        "linger_ms": self.config.linger_ms,
                        "security_protocol": self.config.security_protocol,
                        "value_serializer": lambda v: json.dumps(v).encode("utf-8") if isinstance(v, dict) else v,
                    }
                    if self.config.sasl_mechanism:
                        kwargs["sasl_mechanism"] = self.config.sasl_mechanism
                        kwargs["sasl_plain_username"] = self.config.sasl_plain_username
                        kwargs["sasl_plain_password"] = self.config.sasl_plain_password

                    self._producer = KafkaProducer(**kwargs)
        return self._producer

    def close(self):
        with self._lock:
            if self._producer:
                self._producer.flush()
                self._producer.close()
                self._producer = None

kafka_producer_factory = KafkaProducerFactory.get_instance()
