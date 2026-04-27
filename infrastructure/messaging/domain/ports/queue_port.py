from abc import ABC, abstractmethod
from typing import Any, Tuple
from enum import Enum


class Priority(Enum):
    HIGH = 3
    NORMAL = 2
    LOW = 1


class QueuePort(ABC):
    @abstractmethod
    async def enqueue(self, event: Any, shard_key: Tuple[int, int], priority: Priority) -> bool:
        pass

    @abstractmethod
    def get_queue_depth(self) -> int:
        pass

    @abstractmethod
    def get_stats(self):
        pass
