from typing import List, Optional, Dict, Any

from domain.ports.consumer_port import ConsumerPort, ConsumeParams, ConsumerOffsetParams


class ConsumerDomainClient:
    def __init__(self, consumer_port: ConsumerPort):
        self._consumer = consumer_port

    def consume(self, topic: str, consumer_group: str,
                partition: Optional[int] = None,
                max_messages: int = 10,
                timeout_ms: int = 1000) -> List[Dict[str, Any]]:
        params = ConsumeParams(topic, consumer_group, partition, max_messages, timeout_ms)
        return self._consumer.consume(params)

    def commit_offset(self, consumer_group: str, topic: str,
                     partition: int, offset: int) -> bool:
        params = ConsumerOffsetParams(consumer_group, topic, partition, offset)
        return self._consumer.commit_offset(params)

    def get_offset(self, consumer_group: str, topic: str,
                  partition: int) -> int:
        return self._consumer.get_offset(consumer_group, topic, partition)

    def subscribe(self, topic: str, consumer_group: str) -> bool:
        return self._consumer.subscribe(topic, consumer_group)

    def unsubscribe(self, topic: str, consumer_group: str) -> bool:
        return self._consumer.unsubscribe(topic, consumer_group)

    def list_subscriptions(self, consumer_group: str) -> List[str]:
        return self._consumer.list_subscriptions(consumer_group)

    def close(self):
        close_method = getattr(self._consumer, 'close', None)
        if close_method:
            close_method()
