"""Producer port interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
import asyncio

from shared.types.events import ProduceMessageParams, TopicCreationParams


class ProducerPort(ABC):
    """Port interface for Kafka producer operations"""
    
    @abstractmethod
    def produce(self, params: ProduceMessageParams) -> Dict[str, Any]:
        """Produce a single message"""
        pass

    @abstractmethod
    def produce_async(self, params: ProduceMessageParams) -> asyncio.Future:
        """Produce a message asynchronously"""
        pass

    @abstractmethod
    def produce_batch(self, topic: str, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Produce multiple messages in batch"""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush pending messages"""
        pass

    @abstractmethod
    def list_topics(self) -> List[str]:
        """List available topics"""
        pass

    @abstractmethod
    def create_topic(self, params: TopicCreationParams) -> bool:
        """Create a new topic"""
        pass
