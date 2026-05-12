"""PostgreSQL adapter for DatabasePort."""

import logging
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from infra.ports.database_port import DatabasePort
from shared.types.events import EventRecord, ConsumerOffset
from shared.errors.codes import database_connection_failed, database_query_failed, database_constraint_violation

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class PostgreSQLAdapter(DatabasePort):
    """PostgreSQL adapter implementing DatabasePort with single responsibility"""
    
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._connection = None
    
    def _connect(self):
        """Establish database connection with tracing"""
        with _tracer.start_as_current_span("postgres_connect") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "database-connection")
            span.set_attribute("api.version", "v1")
            
            try:
                self._connection = psycopg2.connect(
                    self._dsn,
                    cursor_factory=RealDictCursor
                )
                span.set_attribute("connection.result", "success")
                logger.info("event=postgres_connect_success")
                return True
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("connection.result", "failed")
                logger.error("event=postgres_connect_failed error=%s", str(e))
                raise database_connection_failed(f"Database connection failed: {str(e)}")
    
    def _ensure_connection(self):
        """Ensure database connection exists"""
        if not self._connection or self._connection.closed:
            self._connect()
    
    def save_event(self, event: EventRecord) -> str:
        """Save a single event"""
        with _tracer.start_as_current_span("save_event") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-storage")
            span.set_attribute("api.version", "v1")
            span.set_attribute("event.topic", event.topic)
            
            self._ensure_connection()
            
            try:
                with self._connection.cursor() as cursor:
                    query = sql.SQL("""
                        INSERT INTO kafka_events (event_id, topic, partition, "offset", key, value, timestamp, headers)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (event_id) DO NOTHING
                        RETURNING id
                    """)
                    
                    cursor.execute(query, (
                        getattr(event, 'event_id', None),
                        event.topic,
                        event.partition,
                        event.offset,
                        event.key,
                        event.value,
                        event.timestamp,
                        event.headers
                    ))
                    
                    result = cursor.fetchone()
                    self._connection.commit()
                    
                    event_id = str(result['id']) if result else None
                    span.set_attribute("save.result", "success" if event_id else "duplicate")
                    span.set_attribute("event.id", event_id)
                    
                    logger.info("event=event_saved topic=%s offset=%d id=%s", event.topic, event.offset, event_id)
                    return event_id
                    
            except psycopg2.IntegrityError as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("save.result", "constraint_violation")
                raise database_constraint_violation(f"Event constraint violation: {str(e)}")
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("save.result", "failed")
                raise database_query_failed(f"Event save failed: {str(e)}")
    
    def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        """Save multiple events in batch"""
        with _tracer.start_as_current_span("save_events_batch") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "batch-event-storage")
            span.set_attribute("api.version", "v1")
            span.set_attribute("batch.size", len(events))
            
            self._ensure_connection()
            
            try:
                with self._connection.cursor() as cursor:
                    query = sql.SQL("""
                        INSERT INTO kafka_events (event_id, topic, partition, "offset", key, value, timestamp, headers)
                        VALUES %s
                        ON CONFLICT (event_id) DO NOTHING
                        RETURNING id
                    """)
                    
                    values = [
                        (
                            getattr(event, 'event_id', None),
                            event.topic,
                            event.partition,
                            event.offset,
                            event.key,
                            event.value,
                            event.timestamp,
                            event.headers
                        )
                        for event in events
                    ]
                    
                    cursor.executemany(query, values)
                    result = cursor.fetchall()
                    self._connection.commit()
                    
                    event_ids = [str(row['id']) for row in result]
                    span.set_attribute("save.result", "success")
                    span.set_attribute("events.saved_count", len(event_ids))
                    
                    logger.info("event=events_batch_saved count=%d", len(event_ids))
                    return event_ids
                    
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("save.result", "failed")
                raise database_query_failed(f"Batch event save failed: {str(e)}")
    
    def get_event(self, event_id: str) -> Optional[EventRecord]:
        """Get event by ID"""
        with _tracer.start_as_current_span("get_event") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-retrieval")
            span.set_attribute("api.version", "v1")
            span.set_attribute("event.id", event_id)
            
            self._ensure_connection()
            
            try:
                with self._connection.cursor() as cursor:
                    query = sql.SQL("""
                        SELECT id, event_id, topic, partition, "offset", key, value, timestamp, headers, processed, error, created_at, updated_at
                        FROM kafka_events
                        WHERE id = %s
                    """)
                    
                    cursor.execute(query, (event_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        event = EventRecord(
                            topic=row['topic'],
                            partition=row['partition'],
                            offset=row['offset'],
                            key=row['key'],
                            value=row['value'],
                            timestamp=row['timestamp'],
                            headers=row['headers'],
                            processed=row['processed'],
                            error=row['error'],
                            created_at=row['created_at']
                        )
                        span.set_attribute("get.result", "found")
                        return event
                    else:
                        span.set_attribute("get.result", "not_found")
                        return None
                        
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("get.result", "failed")
                raise database_query_failed(f"Event get failed: {str(e)}")
    
    def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        """Get events by topic with pagination"""
        with _tracer.start_as_current_span("get_events_by_topic") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-query")
            span.set_attribute("api.version", "v1")
            span.set_attribute("query.topic", topic)
            span.set_attribute("query.limit", limit)
            span.set_attribute("query.offset", offset)
            
            self._ensure_connection()
            
            try:
                with self._connection.cursor() as cursor:
                    query = sql.SQL("""
                        SELECT id, event_id, topic, partition, "offset", key, value, timestamp, headers, processed, error, created_at, updated_at
                        FROM kafka_events
                        WHERE topic = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """)
                    
                    cursor.execute(query, (topic, limit, offset))
                    rows = cursor.fetchall()
                    
                    events = [
                        EventRecord(
                            topic=row['topic'],
                            partition=row['partition'],
                            offset=row['offset'],
                            key=row['key'],
                            value=row['value'],
                            timestamp=row['timestamp'],
                            headers=row['headers'],
                            processed=row['processed'],
                            error=row['error'],
                            created_at=row['created_at']
                        )
                        for row in rows
                    ]
                    
                    span.set_attribute("get.result", "success")
                    span.set_attribute("events.returned_count", len(events))
                    
                    logger.info("event=events_queried topic=%s count=%d", topic, len(events))
                    return events
                    
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("get.result", "failed")
                raise database_query_failed(f"Events query failed: {str(e)}")
    
    def get_unprocessed_events(self, limit: int = 100) -> List[EventRecord]:
        """Get unprocessed events"""
        with _tracer.start_as_current_span("get_unprocessed_events") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-query")
            span.set_attribute("api.version", "v1")
            span.set_attribute("query.limit", limit)
            
            self._ensure_connection()
            
            try:
                with self._connection.cursor() as cursor:
                    query = sql.SQL("""
                        SELECT id, event_id, topic, partition, "offset", key, value, timestamp, headers, processed, error, created_at, updated_at
                        FROM kafka_events
                        WHERE processed = FALSE
                        ORDER BY created_at ASC
                        LIMIT %s
                    """)
                    
                    cursor.execute(query, (limit,))
                    rows = cursor.fetchall()
                    
                    events = [
                        EventRecord(
                            topic=row['topic'],
                            partition=row['partition'],
                            offset=row['offset'],
                            key=row['key'],
                            value=row['value'],
                            timestamp=row['timestamp'],
                            headers=row['headers'],
                            processed=row['processed'],
                            error=row['error'],
                            created_at=row['created_at']
                        )
                        for row in rows
                    ]
                    
                    span.set_attribute("get.result", "success")
                    span.set_attribute("events.returned_count", len(events))
                    
                    logger.info("event=unprocessed_events_queried count=%d", len(events))
                    return events
                    
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("get.result", "failed")
                raise database_query_failed(f"Unprocessed events query failed: {str(e)}")
    
    def mark_event_processed(self, event_id: str, error: Optional[str] = None) -> bool:
        """Mark event as processed"""
        with _tracer.start_as_current_span("mark_event_processed") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-update")
            span.set_attribute("api.version", "v1")
            span.set_attribute("event.id", event_id)
            span.set_attribute("update.error", error is not None)
            
            self._ensure_connection()
            
            try:
                with self._connection.cursor() as cursor:
                    query = sql.SQL("""
                        UPDATE kafka_events
                        SET processed = TRUE, error = %s, updated_at = NOW()
                        WHERE event_id = %s
                    """)
                    
                    cursor.execute(query, (error, event_id))
                    self._connection.commit()
                    
                    span.set_attribute("update.result", "success")
                    logger.info("event=event_marked_processed id=%s error=%s", event_id, error)
                    return True
                    
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("update.result", "failed")
                raise database_query_failed(f"Event mark processed failed: {str(e)}")
    
    def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        """Save consumer offset"""
        with _tracer.start_as_current_span("save_consumer_offset") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "offset-storage")
            span.set_attribute("api.version", "v1")
            span.set_attribute("offset.consumer_group", offset.consumer_group)
            span.set_attribute("offset.topic", offset.topic)
            
            self._ensure_connection()
            
            try:
                with self._connection.cursor() as cursor:
                    query = sql.SQL("""
                        INSERT INTO consumer_offsets (consumer_group, topic, partition, "offset")
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (consumer_group, topic, partition)
                        DO UPDATE SET "offset" = EXCLUDED."offset", updated_at = NOW()
                    """)
                    
                    cursor.execute(query, (
                        offset.consumer_group,
                        offset.topic,
                        offset.partition,
                        offset.offset
                    ))
                    self._connection.commit()
                    
                    span.set_attribute("save.result", "success")
                    logger.info("event=offset_saved group=%s topic=%s partition=%d offset=%d", 
                              offset.consumer_group, offset.topic, offset.partition, offset.offset)
                    return True
                    
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("save.result", "failed")
                raise database_query_failed(f"Consumer offset save failed: {str(e)}")
    
    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[ConsumerOffset]:
        """Get consumer offset"""
        with _tracer.start_as_current_span("get_consumer_offset") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "offset-retrieval")
            span.set_attribute("api.version", "v1")
            span.set_attribute("offset.consumer_group", consumer_group)
            span.set_attribute("offset.topic", topic)
            
            self._ensure_connection()
            
            try:
                with self._connection.cursor() as cursor:
                    query = sql.SQL("""
                        SELECT consumer_group, topic, partition, "offset", updated_at
                        FROM consumer_offsets
                        WHERE consumer_group = %s AND topic = %s AND partition = %s
                    """)
                    
                    cursor.execute(query, (consumer_group, topic, partition))
                    row = cursor.fetchone()
                    
                    if row:
                        offset = ConsumerOffset(
                            consumer_group=row['consumer_group'],
                            topic=row['topic'],
                            partition=row['partition'],
                            offset=row['offset'],
                            updated_at=row['updated_at']
                        )
                        span.set_attribute("get.result", "found")
                        return offset
                    else:
                        span.set_attribute("get.result", "not_found")
                        return None
                        
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("get.result", "failed")
                raise database_query_failed(f"Consumer offset get failed: {str(e)}")
    
    def delete_events_by_topic(self, topic: str) -> int:
        """Delete events by topic"""
        with _tracer.start_as_current_span("delete_events_by_topic") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-deletion")
            span.set_attribute("api.version", "v1")
            span.set_attribute("delete.topic", topic)
            
            self._ensure_connection()
            
            try:
                with self._connection.cursor() as cursor:
                    query = sql.SQL("DELETE FROM kafka_events WHERE topic = %s")
                    cursor.execute(query, (topic,))
                    count = cursor.rowcount
                    self._connection.commit()
                    
                    span.set_attribute("delete.result", "success")
                    span.set_attribute("events.deleted_count", count)
                    
                    logger.info("event=events_deleted topic=%s count=%d", topic, count)
                    return count
                    
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("delete.result", "failed")
                raise database_query_failed(f"Events delete failed: {str(e)}")
    
    def get_event_count(self, topic: Optional[str] = None) -> int:
        """Get event count"""
        with _tracer.start_as_current_span("get_event_count") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-count")
            span.set_attribute("api.version", "v1")
            if topic:
                span.set_attribute("count.topic", topic)
            
            self._ensure_connection()
            
            try:
                with self._connection.cursor() as cursor:
                    if topic:
                        query = sql.SQL("SELECT COUNT(*) FROM kafka_events WHERE topic = %s")
                        cursor.execute(query, (topic,))
                    else:
                        query = sql.SQL("SELECT COUNT(*) FROM kafka_events")
                        cursor.execute(query)
                    
                    count = cursor.fetchone()[0]
                    
                    span.set_attribute("count.result", "success")
                    span.set_attribute("events.count", count)
                    
                    logger.info("event=events_counted topic=%s count=%d", topic or "all", count)
                    return count
                    
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("count.result", "failed")
                raise database_query_failed(f"Event count failed: {str(e)}")
    
    def close(self) -> None:
        """Close database connection"""
        with _tracer.start_as_current_span("close_database") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "database-cleanup")
            span.set_attribute("api.version", "v1")
            
            if self._connection and not self._connection.closed:
                try:
                    self._connection.close()
                    span.set_attribute("close.result", "success")
                    logger.info("event=database_closed")
                except Exception as e:
                    span.record_error(e)
                    span.set_attribute("close.result", "failed")
                    logger.error("event=database_close_failed error=%s", str(e))
