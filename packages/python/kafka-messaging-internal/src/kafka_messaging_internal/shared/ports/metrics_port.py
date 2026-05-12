"""Metrics port interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class MetricsPort(ABC):
    """Port interface for metrics collection and reporting"""
    
    @abstractmethod
    def increment_counter(self, name: str, value: Union[int, float] = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric"""
        pass
    
    @abstractmethod
    def record_histogram(self, name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram value"""
        pass
    
    @abstractmethod
    def set_gauge(self, name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge value"""
        pass
    
    @abstractmethod
    def record_timing(self, name: str, duration_ms: Union[int, float], tags: Optional[Dict[str, str]] = None) -> None:
        """Record timing/duration"""
        pass
    
    @abstractmethod
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event metric"""
        pass
    
    @abstractmethod
    def create_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Any:
        """Create a span for tracing"""
        pass
    
    @abstractmethod
    def finish_span(self, span: Any, error: Optional[Exception] = None) -> None:
        """Finish a span with optional error"""
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Flush metrics"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close metrics connection"""
        pass
