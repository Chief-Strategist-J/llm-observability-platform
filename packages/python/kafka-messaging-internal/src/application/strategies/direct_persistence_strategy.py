"""Direct persistence strategy with single responsibility."""

import logging
from typing import List
from opentelemetry import trace

from infra.ports.database_port import DatabasePort
from shared.types.events import EventRecord

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class DirectPersistenceStrategy:
    """Strategy for direct database persistence with single responsibility"""
    
    def __init__(self, database: DatabasePort):
        self._database = database
    
    async def save(self, event: EventRecord) -> str:
        """Save event directly to database"""
        with _tracer.start_as_current_span("direct_persistence_save") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "persistence-strategy")
            span.set_attribute("api.version", "v1")
            span.set_attribute("strategy.type", "direct")
            span.set_attribute("event.topic", event.topic)
            
            try:
                event_id = self._database.save_event(event)
                span.set_attribute("save.result", "success")
                span.set_attribute("event.id", event_id)
                
                logger.info("event=strategy_save_direct topic=%s id=%s", event.topic, event_id)
                return event_id
                
            except Exception as e:
                span.record_error(e)
                span.set_attribute("save.result", "failed")
                logger.error("event=strategy_save_direct_failed topic=%s error=%s", event.topic, str(e))
                raise
    
    async def save_batch(self, events: List[EventRecord]) -> List[str]:
        """Save events directly to database in batch"""
        with _tracer.start_as_current_span("direct_persistence_save_batch") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "persistence-strategy")
            span.set_attribute("api.version", "v1")
            span.set_attribute("strategy.type", "direct")
            span.set_attribute("batch.size", len(events))
            
            try:
                event_ids = self._database.save_events_batch(events)
                span.set_attribute("save.result", "success")
                span.set_attribute("events.saved_count", len(event_ids))
                
                logger.info("event=strategy_save_batch_direct count=%d", len(event_ids))
                return event_ids
                
            except Exception as e:
                span.record_error(e)
                span.set_attribute("save.result", "failed")
                logger.error("event=strategy_save_batch_direct_failed count=%d error=%s", len(events), str(e))
                raise
