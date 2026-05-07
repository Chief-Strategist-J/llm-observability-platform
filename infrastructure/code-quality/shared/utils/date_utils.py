from datetime import datetime, timezone
from typing import Optional


class DateUtils:
    
    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def from_timestamp(timestamp: float) -> datetime:
        return datetime.fromtimestamp(timestamp, timezone.utc)

    @staticmethod
    def to_timestamp(dt: datetime) -> float:
        return dt.timestamp()

    @staticmethod
    def format_duration(start_time: datetime, end_time: datetime) -> str:
        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    @staticmethod
    def is_within_last_hours(dt: datetime, hours: int) -> bool:
        now = DateUtils.utc_now()
        time_diff = now - dt
        return time_diff.total_seconds() <= hours * 3600

    @staticmethod
    def is_within_last_days(dt: datetime, days: int) -> bool:
        now = DateUtils.utc_now()
        time_diff = now - dt
        return time_diff.total_seconds() <= days * 24 * 3600

    @staticmethod
    def format_iso(dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        return dt.isoformat()

    @staticmethod
    def parse_iso(date_str: Optional[str]) -> Optional[datetime]:
        if date_str is None:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            return None
