"""Queue-based persistence strategy with single responsibility."""

import logging
from typing import Any, List, Tuple, Callable
from opentelemetry import trace

from infra.ports.database_port import DatabasePort
from shared.types.events import EventRecord

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class QueuePersistenceStrategy:
    """Strategy for queue-based persistence with single responsibility"""
    
    def __init__(self, database: DatabasePort, shard_key_getter: Callable):
        self._database = database
        self._shard_key_getter = shard_key_getter
    
    async def save(self, event: EventRecord) -> str:
        """Save event via queue with sharding"""
        with _tracer.start_as_current_span("queue_persistence_save") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "persistence-strategy")
            span.set_attribute("api.version", "v1")
            span.set_attribute("strategy.type", "queue")
            span.set_attribute("event.topic", event.topic)
            
            try:
                # Get shard key for event
                shard_key = self._shard_key_getter(event.key)
                
                # In a real implementation, this would enqueue to a queue
                # For now, we'll simulate and save directly
                event_id = self._database.save_event(event)
                
                span.set_attribute("save.result", "success")
                span.set_attribute("event.id", event_id)
                span.set_attribute("shard.key", f"{shard_key[0]}-{shard_key[1]}")
                
                logger.info("event=strategy_save_queue topic=%s id=%s shard=%s", 
                          event.topic, event_id, f"{shard_key[0]}-{shard_key[1]}")
                
                return f"queued-{shard_key[0]}-{shard_key[1]}"
                
            except Exception as e:
                span.record_error(e)
                span.set_attribute("save.result", "failed")
                logger.error("event=strategy_save_queue_failed topic=%s error=%s", event.topic, str(e))
                raise
    
    async def save_batch(self, events: List[EventRecord]) -> List[str]:
        """Save events via queue with sharding"""
        with _tracer.start_as_current_span("queue_persistence_save_batch") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "persistence-strategy")
            span.set_attribute("api.version", "v1")
            span.set_attribute("strategy.type", "queue")
            span.set_attribute("batch.size", len(events))
            
            try:
                results = []
                
                # Process each event with sharding
                for event in events:
                    event_id = await self.save(event)
                    results.append(event_id)
                
                span.set_attribute("save.result", "success")
                span.set_attribute("events.saved_count", len(results))
                
                logger.info("event=strategy_save_batch_queue count=%d", len(results))
                return results
                
            except Exception as e:
                span.record_error(e)
                span.set_attribute("save.result", "failed")
                logger.error("event=strategy_save_batch_queue_failed count=%d error=%s", len(events), str(e))
                raise
