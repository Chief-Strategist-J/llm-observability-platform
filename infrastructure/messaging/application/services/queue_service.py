from typing import Any, Tuple
from domain.ports.queue_port import QueuePort
from domain.ports.metrics_port import MetricsPort
from infrastructure.queue.in_memory_queue import Priority
from application.api.v1.error_handler import raise_too_many_requests_error


class QueueService:
    def __init__(self, queue: QueuePort, metrics: MetricsPort = None):
        self._queue = queue
        self._metrics = metrics

    async def enqueue_event(self, event: Any, shard_key: Tuple[int, int], priority: str = "normal") -> bool:
        from infrastructure.queue.in_memory_queue import Priority
        priority_map = {"high": Priority.HIGH, "normal": Priority.NORMAL, "low": Priority.LOW}
        priority_enum = priority_map.get(priority, Priority.NORMAL)

        enqueued = await self._queue.enqueue(event, shard_key, priority_enum)

        if self._metrics:
            self._metrics.record_request()
            self._metrics.record_queue_depth(self._queue.get_queue_depth())

        if not enqueued:
            if self._metrics:
                self._metrics.record_rejection()
            raise_too_many_requests_error("Queue full, please retry later")

        return True
