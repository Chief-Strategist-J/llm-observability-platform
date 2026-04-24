from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio


class ProducerPort(ABC):
    @abstractmethod
    def produce(self, topic: str, key: Optional[str], value: Any, partition: Optional[int], headers: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def produce_batch(self, topic: str, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def produce_async(self, topic: str, key: Optional[str], value: Any, partition: Optional[int], headers: Optional[Dict[str, Any]]) -> asyncio.Future:
        pass

    @abstractmethod
    def flush(self, timeout: float = 10.0) -> None:
        pass

    @abstractmethod
    def list_topics(self) -> List[str]:
        pass

    @abstractmethod
    def create_topic(self, topic_name: str, partitions: int, replication_factor: int) -> bool:
        pass
