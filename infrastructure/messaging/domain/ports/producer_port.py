from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio
from dataclasses import dataclass


@dataclass
class ProduceMessageParams:
    topic: str
    key: Optional[str]
    value: Any
    partition: Optional[int]
    headers: Optional[Dict[str, Any]]


@dataclass
class TopicCreationParams:
    topic_name: str
    partitions: int
    replication_factor: int


class ProducerPort(ABC):
    @abstractmethod
    def produce(self, params: ProduceMessageParams) -> Dict[str, Any]:
        pass

    @abstractmethod
    def produce_async(self, params: ProduceMessageParams) -> asyncio.Future:
        pass

    @abstractmethod
    def produce_batch(self, topic: str, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def flush(self) -> None:
        pass

    @abstractmethod
    def list_topics(self) -> List[str]:
        pass

    @abstractmethod
    def create_topic(self, params: TopicCreationParams) -> bool:
        pass
