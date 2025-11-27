"""
Pure functional metrics module for observability client  

This module provides functional, composable metrics utilities.
"""

from typing import Dict, Any, Protocol
from opentelemetry import metrics as otel_metrics
from opentelemetry.metrics import Meter


# Type aliases
Attributes = Dict[str, Any]


class MetricRecorder(Protocol):
    """Protocol for metric recording functions"""
    def record(self, name: str, value: float, attrs: Attributes) -> None:
        ...


def create_counter(meter: Meter, name: str, description: str = ""):
    """
    Create a counter metric
    
    Pure function: Returns a counter instrument
    """
    return meter.create_counter(
        name=name,
        description=description or f"Counter for {name}"
    )


def create_histogram(meter: Meter, name: str, description: str = ""):
    """
    Create a histogram metric
    
    Pure function: Returns a histogram instrument
    """
    return meter.create_histogram(
        name=name,
        description=description or f"Histogram for {name}"
    )


def record_counter(
    counter,
    value: int = 1,
    attributes: Attributes = None
) -> None:
    """
    Record a counter value
    
    Pure action: Predictable side effect
    """
    counter.add(value, attributes=attributes or {})


def record_histogram(
    histogram,
    value: float,
    attributes: Attributes = None
) -> None:
    """
    Record a histogram value
    
    Pure action: Predictable side effect
    """
    histogram.record(value, attributes=attributes or {})


class MetricsClient:
    """
    Metrics client with functional core
    
    Maintains metric instruments and provides clean API
    """
    
    def __init__(self, meter: Meter):
        self.meter = meter
        self._counters = {}
        self._histograms = {}
    
    def counter(
        self,
        name: str,
        value: int = 1,
        attributes: Attributes = None,
        description: str = ""
    ) -> None:
        """Increment a counter metric"""
        if name not in self._counters:
            self._counters[name] = create_counter(self.meter, name, description)
        
        record_counter(self._counters[name], value, attributes)
    
    def histogram(
        self,
        name: str,
        value: float,
        attributes: Attributes = None,
        description: str = ""
    ) -> None:
        """Record a histogram value"""
        if name not in self._histograms:
            self._histograms[name] = create_histogram(self.meter, name, description)
        
        record_histogram(self._histograms[name], value, attributes)
    
    def gauge(
        self,
        name: str,
        value: float,
        attributes: Attributes = None,
        description: str = ""
    ) -> None:
        """
        Set a gauge value
        
        Note: Gauges in OTel are observable, so we create them differently
        """
        # For gauges, we'd need to use observable gauges with callbacks
        # This is a simplified implementation
        pass
