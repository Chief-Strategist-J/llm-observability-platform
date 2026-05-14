"""Database operations service."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from kafka_messaging_internal.shared.ports.database_port import DatabasePort


class DatabaseOperationsService:
    """Service for database operations following SRP rules."""
    
    def __init__(self, database: DatabasePort):
        """Initialize database operations service."""
        self.database = database
    
    async def get_event_count(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get event count with optional filters."""
        try:
            topic = filters.get('topic')
            if topic:
                count = await self.database.get_event_count(topic)
            else:
                count = await self.database.get_event_count()
            
            return {
                "count": count,
                "topic": topic,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "count": 0,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def delete_events_by_topic(self, topic: str) -> Dict[str, Any]:
        """Delete events by topic."""
        try:
            if not topic:
                return {
                    "success": False,
                    "error": "Topic is required",
                    "deleted_count": 0
                }
            
            deleted_count = await self.database.delete_events_by_topic(topic)
            
            return {
                "success": True,
                "topic": topic,
                "deleted_count": deleted_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "deleted_count": 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_unprocessed_events(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get unprocessed events."""
        try:
            limit = filters.get('limit', 100)
            if not isinstance(limit, int) or limit <= 0:
                limit = 100
            
            events = await self.database.get_unprocessed_events(limit)
            
            return {
                "events": [event.to_dict() if hasattr(event, 'to_dict') else str(event) for event in events],
                "count": len(events),
                "limit": limit,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "events": [],
                "count": 0,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
