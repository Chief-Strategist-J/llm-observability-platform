"""Pure datetime utilities with no side effects."""

from datetime import datetime, timezone
from typing import Union, Optional
import re


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def format_timestamp(dt: datetime, format_type: str = 'iso') -> str:
    """Format datetime to string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    if format_type == 'iso':
        return dt.isoformat().replace('+00:00', 'Z')
    elif format_type == 'unix':
        return str(int(dt.timestamp()))
    elif format_type == 'unix_ms':
        return str(int(dt.timestamp() * 1000))
    else:
        raise ValueError(f"Unsupported format type: {format_type}")


def parse_timestamp(timestamp: Union[str, int, float]) -> datetime:
    """Parse timestamp from various formats."""
    if isinstance(timestamp, datetime):
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp
    
    elif isinstance(timestamp, str):
        # Try ISO format first
        iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        if re.match(iso_pattern, timestamp):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                pass
        
        # Try Unix timestamp (seconds)
        if timestamp.isdigit():
            return datetime.fromtimestamp(int(timestamp), timezone.utc)
        
        # Try Unix timestamp (milliseconds)
        if timestamp.replace('.', '').isdigit():
            return datetime.fromtimestamp(float(timestamp) / 1000, timezone.utc)
        
        raise ValueError(f"Unable to parse timestamp string: {timestamp}")
    
    elif isinstance(timestamp, (int, float)):
        # Determine if seconds or milliseconds
        if timestamp > 1e12:  # Milliseconds
            return datetime.fromtimestamp(timestamp / 1000, timezone.utc)
        else:  # Seconds
            return datetime.fromtimestamp(timestamp, timezone.utc)
    
    else:
        raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")


def calculate_duration(start_time: datetime, end_time: Optional[datetime] = None) -> float:
    """Calculate duration in seconds between two datetimes."""
    if end_time is None:
        end_time = utc_now()
    
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    
    return (end_time - start_time).total_seconds()


def is_recent(dt: datetime, seconds: int = 300) -> bool:
    """Check if datetime is within the last N seconds."""
    now = utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return (now - dt).total_seconds() <= seconds


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"
