from __future__ import annotations


class LatencyQueryError(Exception):
    """Base error for all latency query feature errors."""


class SketchNotFoundError(LatencyQueryError):
    """Raised when no DDSketch exists for the requested model/hour."""


class SLODataNotFoundError(LatencyQueryError):
    """Raised when no SLO keys exist for the requested model/endpoint."""


class BaselineNotFoundError(LatencyQueryError):
    """Raised when ClickHouse returns no rows for the requested model/hour/days."""


class InvalidQuantileError(LatencyQueryError):
    """Raised when a requested quantile is out of the valid range (0, 1)."""
