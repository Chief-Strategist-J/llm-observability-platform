from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass


@dataclass
class ConsumeParams:
    topic: str
    consumer_group: str
    partition: Optional[int]
    max_messages: int
    timeout_ms: int


@dataclass
class ParallelConsumeParams:
    topic: str
    consumer_group: str
    partitions: List[int]
    max_messages_per_partition: int
    timeout_ms: int


@dataclass
class ConsumerOffsetParams:
    consumer_group: str
    topic: str
    partition: int
    offset: int


class ConsumerPort(ABC):
    @abstractmethod
    def consume(self, params: ConsumeParams) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def consume_parallel(self, params: ParallelConsumeParams) -> Dict[int, List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def consume_stream(self, topic: str, consumer_group: str, message_handler: Callable, batch_size: int = 100) -> None:
        pass

    @abstractmethod
    def stop_stream(self) -> None:
        pass

    @abstractmethod
    def commit_offset(self, params: ConsumerOffsetParams) -> bool:
        pass

    @abstractmethod
    def commit_offsets_batch(self, offsets: Dict[str, Dict[int, int]]) -> Dict[str, bool]:
        pass

    @abstractmethod
    def get_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[int]:
        pass

    @abstractmethod
    def subscribe(self, topic: str, consumer_group: str) -> bool:
        pass

    @abstractmethod
    def unsubscribe(self, topic: str, consumer_group: str) -> bool:
        pass

    @abstractmethod
    def list_subscriptions(self, consumer_group: str) -> List[str]:
        pass
