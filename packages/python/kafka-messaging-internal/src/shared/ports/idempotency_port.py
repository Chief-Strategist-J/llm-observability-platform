"""Idempotency port interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class IdempotencyPort(ABC):
    """Port interface for idempotency checking"""
    
    @abstractmethod
    def check_and_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Check if key exists and set if not. Returns True if key was set (first time)"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key"""
        pass
    
    @abstractmethod
    def clear_expired(self) -> int:
        """Clear expired keys"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close idempotency store connection"""
        pass
