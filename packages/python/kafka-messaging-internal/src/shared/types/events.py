from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class EventRecord:
    """Domain entity representing a Kafka event record"""
    topic: str
    partition: int
    offset: int
    key: Optional[str]
    value: Any
    timestamp: datetime
    headers: Optional[Dict[str, Any]] = None
    processed: bool = False
    error: Optional[str] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class ConsumerOffset:
    """Domain entity representing consumer offset information"""
    consumer_group: str
    topic: str
    partition: int
    offset: int
    updated_at: datetime = None

    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class ProduceMessageParams:
    """Parameters for producing a message"""
    topic: str
    key: Optional[str]
    value: Any
    partition: Optional[int]
    headers: Optional[Dict[str, Any]]


@dataclass
class TopicCreationParams:
    """Parameters for creating a topic"""
    topic_name: str
    partitions: int
    replication_factor: int


@dataclass
class ConsumeParams:
    """Parameters for consuming messages"""
    topic: str
    consumer_group: str
    partition: Optional[int]
    max_messages: int
    timeout_ms: int


@dataclass
class ParallelConsumeParams:
    """Parameters for parallel consumption"""
    topic: str
    consumer_group: str
    partitions: List[int]
    max_messages_per_partition: int
    timeout_ms: int


@dataclass
class ConsumerOffsetParams:
    """Parameters for consumer offset operations"""
    consumer_group: str
    topic: str
    partition: int
    offset: int
