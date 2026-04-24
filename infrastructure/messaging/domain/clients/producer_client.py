from typing import List, Optional, Dict, Any

from infrastructure.messaging.domain.ports.producer_port import ProducerPort


class ProducerDomainClient:
    def __init__(self, producer_port: ProducerPort):
        self._producer = producer_port
    
    def produce(self, topic: str, value: Any, key: Optional[str] = None,
               partition: Optional[int] = None,
               headers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._producer.produce(topic, key, value, partition, headers)
    
    def list_topics(self) -> List[str]:
        return self._producer.list_topics()
    
    def create_topic(self, topic_name: str, partitions: int = 1,
                    replication_factor: int = 1) -> bool:
        return self._producer.create_topic(topic_name, partitions, replication_factor)
    
    def close(self):
        if hasattr(self._producer, 'close'):
            self._producer.close()
