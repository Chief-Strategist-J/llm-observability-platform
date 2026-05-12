"""Type definitions for database operations feature."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EventCountRequest(BaseModel):
    """Request model for event count queries."""
    topic: Optional[str] = Field(None, description="Filter by topic name")


class EventCountResponse(BaseModel):
    """Response model for event count."""
    count: int = Field(..., description="Total number of events")
    topic: Optional[str] = Field(None, description="Topic filter applied")


class DeleteEventsRequest(BaseModel):
    """Request model for event deletion."""
    topic: str = Field(..., min_length=1, max_length=255, description="Topic name to delete events from")


class DeleteEventsResponse(BaseModel):
    """Response model for event deletion."""
    topic: str = Field(..., description="Topic name events were deleted from")
    deleted_count: int = Field(..., description="Number of events deleted")
    success: bool = Field(..., description="Deletion success status")


class UnprocessedEventsRequest(BaseModel):
    """Request model for unprocessed events query."""
    limit: int = Field(100, ge=1, le=1000, description="Maximum events to return")


class UnprocessedEventsResponse(BaseModel):
    """Response model for unprocessed events."""
    events: List[Dict[str, Any]] = Field(..., description="Unprocessed event records")
    count: int = Field(..., description="Number of events returned")
    limit: int = Field(..., description="Limit applied to query")
