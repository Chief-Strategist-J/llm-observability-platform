"""Consumer port interface."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

from shared.types.events import ConsumeParams, ParallelConsumeParams, ConsumerOffsetParams


class ConsumerPort(ABC):
    """Port interface for Kafka consumer operations"""
    
    @abstractmethod
    def consume(self, params: ConsumeParams) -> List[Dict[str, Any]]:
        """Consume messages"""
        pass

    @abstractmethod
    def consume_parallel(self, params: ParallelConsumeParams) -> Dict[int, List[Dict[str, Any]]]:
        """Consume messages in parallel from multiple partitions"""
        pass

    @abstractmethod
    def consume_stream(self, topic: str, consumer_group: str, message_handler: Callable, batch_size: int = 100) -> None:
        """Start streaming consumption"""
        pass

    @abstractmethod
    def stop_stream(self) -> None:
        """Stop streaming consumption"""
        pass

    @abstractmethod
    def commit_offset(self, params: ConsumerOffsetParams) -> bool:
        """Commit consumer offset"""
        pass

    @abstractmethod
    def commit_offsets_batch(self, offsets: Dict[str, Dict[int, int]]) -> Dict[str, bool]:
        """Commit multiple offsets in batch"""
        pass

    @abstractmethod
    def get_offset(self, consumer_group: str, topic: str, partition: int) -> int:
        """Get current offset for consumer"""
        pass

    @abstractmethod
    def subscribe(self, topic: str, consumer_group: str) -> bool:
        """Subscribe to a topic"""
        pass

    @abstractmethod
    def unsubscribe(self, topic: str, consumer_group: str) -> bool:
        """Unsubscribe from a topic"""
        pass

    @abstractmethod
    def list_subscriptions(self, consumer_group: str) -> List[str]:
        """List subscriptions for consumer group"""
        pass
