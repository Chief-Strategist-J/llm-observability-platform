"""Queue port interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class QueuePort(ABC):
    """Port interface for queue operations"""
    
    @abstractmethod
    def enqueue(self, queue_name: str, message: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Enqueue message"""
        pass
    
    @abstractmethod
    def dequeue(self, queue_name: str, timeout: Optional[int] = None) -> Optional[Any]:
        """Dequeue message"""
        pass
    
    @abstractmethod
    def dequeue_batch(self, queue_name: str, batch_size: int, timeout: Optional[int] = None) -> List[Any]:
        """Dequeue multiple messages"""
        pass
    
    @abstractmethod
    def acknowledge(self, queue_name: str, message_id: str) -> bool:
        """Acknowledge message processing"""
        pass
    
    @abstractmethod
    def reject(self, queue_name: str, message_id: str, requeue: bool = True) -> bool:
        """Reject message"""
        pass
    
    @abstractmethod
    def get_queue_size(self, queue_name: str) -> int:
        """Get queue size"""
        pass
    
    @abstractmethod
    def purge_queue(self, queue_name: str) -> int:
        """Purge all messages from queue"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close queue connection"""
        pass
