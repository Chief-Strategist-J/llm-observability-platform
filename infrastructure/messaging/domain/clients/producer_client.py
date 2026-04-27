from typing import List, Optional, Dict, Any

from domain.ports.producer_port import ProducerPort, ProduceMessageParams, TopicCreationParams


class ProducerDomainClient:
    def __init__(self, producer_port: ProducerPort):
        self._producer = producer_port

    def produce(self, topic: str, value: Any, key: Optional[str] = None,
               partition: Optional[int] = None,
               headers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = ProduceMessageParams(topic, key, value, partition, headers)
        return self._producer.produce(params)

    def list_topics(self) -> List[str]:
        return self._producer.list_topics()

    def create_topic(self, topic_name: str, partitions: int = 1,
                    replication_factor: int = 1) -> bool:
        params = TopicCreationParams(topic_name, partitions, replication_factor)
        return self._producer.create_topic(params)

    def close(self):
        close_method = getattr(self._producer, 'close', None)
        if close_method:
            close_method()
