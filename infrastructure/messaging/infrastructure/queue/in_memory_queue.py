import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import time
from domain.ports.queue_port import QueuePort


class Priority(Enum):
    HIGH = 3
    NORMAL = 2
    LOW = 1


@dataclass(order=True)
class QueuedItem:
    priority: int = field(compare=True)
    timestamp: float = field(compare=True)
    event: Any = field(compare=False)
    shard_key: Tuple[int, int] = field(compare=False)

    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


@dataclass
class QueueConfig:
    max_size: int = 100_000
    per_shard_limit: int = 10_000
    enable_priority: bool = True


@dataclass
class QueueStats:
    total_size: int = 0
    dropped_count: int = 0
    per_shard_sizes: Dict[Tuple[int, int], int] = field(default_factory=dict)
    rejection_count: int = 0


class InMemoryQueue(QueuePort):
    def __init__(self, config: Optional[QueueConfig] = None):
        self.config = config or QueueConfig()
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=self.config.max_size)
        self._per_shard_counts: Dict[Tuple[int, int], int] = {}
        self._lock = asyncio.Lock()
        self._stats = QueueStats()

    async def enqueue(self, event: Any, shard_key: Tuple[int, int], priority: Priority = Priority.NORMAL) -> bool:
        async with self._lock:
            current_shard_count = self._per_shard_counts.get(shard_key, 0)

            if current_shard_count >= self.config.per_shard_limit:
                self._stats.dropped_count += 1
                self._stats.rejection_count += 1
                return False

            if self._queue.full():
                if self.config.enable_priority and priority == Priority.HIGH:
                    try:
                        await self._evict_low_priority()
                    except asyncio.QueueEmpty:
                        self._stats.dropped_count += 1
                        self._stats.rejection_count += 1
                        return False
                else:
                    self._stats.dropped_count += 1
                    self._stats.rejection_count += 1
                    return False

            item = QueuedItem(
                priority=priority.value,
                event=event,
                shard_key=shard_key
            )

            try:
                self._queue.put_nowait(item)
                self._per_shard_counts[shard_key] = current_shard_count + 1
                self._stats.total_size = self._queue.qsize()
                self._stats.per_shard_sizes = self._per_shard_counts.copy()
                return True
            except asyncio.QueueFull:
                self._stats.dropped_count += 1
                self._stats.rejection_count += 1
                return False

    async def dequeue(self, timeout: Optional[float] = None) -> Optional[QueuedItem]:
        try:
            if timeout:
                item = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            else:
                item = await self._queue.get()

            async with self._lock:
                shard_key = item.shard_key
                current_count = self._per_shard_counts.get(shard_key, 0)
                if current_count > 0:
                    self._per_shard_counts[shard_key] = current_count - 1
                self._stats.total_size = self._queue.qsize()
                self._stats.per_shard_sizes = self._per_shard_counts.copy()

            return item
        except asyncio.TimeoutError:
            return None

    async def dequeue_batch(self, batch_size: int, timeout: Optional[float] = None) -> List[QueuedItem]:
        items = []
        for _ in range(batch_size):
            item = await self.dequeue(timeout)
            if item is None:
                break
            items.append(item)
        return items

    async def _evict_low_priority(self):
        temp_items = []
        evicted = False

        while not self._queue.empty() and not evicted:
            item = self._queue.get_nowait()
            if item.priority == Priority.LOW.value:
                evicted = True
                shard_key = item.shard_key
                current_count = self._per_shard_counts.get(shard_key, 0)
                if current_count > 0:
                    self._per_shard_counts[shard_key] = current_count - 1
            else:
                temp_items.append(item)

        for temp_item in temp_items:
            self._queue.put_nowait(temp_item)

        if not evicted:
            raise asyncio.QueueEmpty()

    def get_stats(self) -> QueueStats:
        self._stats.total_size = self._queue.qsize()
        self._stats.per_shard_sizes = self._per_shard_counts.copy()
        return self._stats

    def get_queue_depth(self) -> int:
        return self._queue.qsize()

    def get_per_shard_depth(self, shard_key: Tuple[int, int]) -> int:
        return self._per_shard_counts.get(shard_key, 0)

    def is_full(self) -> bool:
        return self._queue.full()

    def is_shard_overloaded(self, shard_key: Tuple[int, int]) -> bool:
        return self._per_shard_counts.get(shard_key, 0) >= self.config.per_shard_limit

    async def clear(self) -> None:
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        self._per_shard_counts.clear()
        self._stats = QueueStats()

    def get_capacity_usage(self) -> float:
        return self._queue.qsize() / self.config.max_size if self.config.max_size > 0 else 0.0
