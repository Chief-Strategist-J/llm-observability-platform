from abc import ABC, abstractmethod
from typing import Optional


class CountPort(ABC):
    @abstractmethod
    def get_event_count(self, topic: Optional[str] = None) -> int:
        pass
