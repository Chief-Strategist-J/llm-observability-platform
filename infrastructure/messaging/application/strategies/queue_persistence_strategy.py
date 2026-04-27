from typing import Any, Tuple
from domain.ports.persistence_strategy import PersistenceStrategy
from domain.ports.database_port import EventRecord
from application.services.queue_service import QueueService


class QueuePersistenceStrategy(PersistenceStrategy):
    def __init__(self, queue_service: QueueService, shard_key_getter):
        self._queue_service = queue_service
        self._shard_key_getter = shard_key_getter

    async def save(self, event: EventRecord) -> str:
        shard_key = self._shard_key_getter(event.key)
        await self._queue_service.enqueue_event(event, shard_key, "normal")
        return f"queued-{shard_key[0]}-{shard_key[1]}"

    async def save_batch(self, events: list) -> list:
        results = []
        for event in events:
            event_id = await self.save(event)
            results.append(event_id)
        return results
