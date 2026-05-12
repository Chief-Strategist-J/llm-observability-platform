"""Type definitions for event processing feature."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class EventProcessingRequest(BaseModel):
    """Request model for event processing."""
    event_id: Optional[str] = Field(None, description="Unique event identifier")
    topic: str = Field(..., description="Kafka topic name")
    partition: int = Field(..., ge=0, description="Partition number")
    offset: int = Field(..., ge=0, description="Message offset")
    key: Optional[str] = Field(None, description="Message key")
    value: Any = Field(..., description="Message value")
    timestamp: datetime = Field(..., description="Event timestamp")
    headers: Optional[Dict[str, Any]] = Field(None, description="Message headers")


class BatchEventProcessingRequest(BaseModel):
    """Request model for batch event processing."""
    records: List[EventProcessingRequest] = Field(..., min_items=1, max_items=1000)


class EventProcessingResponse(BaseModel):
    """Response model for event processing."""
    event_id: str = Field(..., description="Processed event ID")
    success: bool = Field(..., description="Processing success status")
    result: Optional[Dict[str, Any]] = Field(None, description="Processing result")
    error: Optional[str] = Field(None, description="Error message if failed")


class BatchEventProcessingResponse(BaseModel):
    """Response model for batch event processing."""
    event_ids: List[str] = Field(..., description="Processed event IDs")
    count: int = Field(..., description="Number of events processed")
    success: bool = Field(..., description="Overall batch success status")


class EventQueryRequest(BaseModel):
    """Request model for event queries."""
    topic: Optional[str] = Field(None, description="Filter by topic")
    limit: int = Field(100, ge=1, le=1000, description="Maximum events to return")
    offset: int = Field(0, ge=0, description="Pagination offset")


class EventQueryResponse(BaseModel):
    """Response model for event queries."""
    events: List[Dict[str, Any]] = Field(..., description="Event records")
    count: int = Field(..., description="Number of events returned")
    has_more: bool = Field(..., description="Whether more events are available")


class ConsumerOffsetRequest(BaseModel):
    """Request model for consumer offset updates."""
    consumer_group: str = Field(..., description="Consumer group name")
    topic: str = Field(..., description="Kafka topic name")
    partition: int = Field(..., ge=0, description="Partition number")
    offset: int = Field(..., ge=0, description="Consumer offset")


class ConsumerOffsetResponse(BaseModel):
    """Response model for consumer offset operations."""
    consumer_group: str = Field(..., description="Consumer group name")
    topic: str = Field(..., description="Kafka topic name")
    partition: int = Field(..., description="Partition number")
    offset: int = Field(..., description="Consumer offset")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ConsumerOffsetsQueryRequest(BaseModel):
    """Request model for consumer offset queries."""
    consumer_group: str = Field(..., description="Consumer group name")
    topic: Optional[str] = Field(None, description="Filter by topic")


class ConsumerOffsetsResponse(BaseModel):
    """Response model for consumer offset queries."""
    offsets: List[ConsumerOffsetResponse] = Field(..., description="Consumer offset records")
