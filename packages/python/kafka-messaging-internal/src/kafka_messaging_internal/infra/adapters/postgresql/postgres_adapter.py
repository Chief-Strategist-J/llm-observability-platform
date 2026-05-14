"""PostgreSQL adapter implementing DatabasePort interface."""

import json
import psycopg2
from psycopg2 import pool, extras
from typing import Any, Dict, List, Optional
from datetime import datetime

from opentelemetry import trace
from kafka_messaging_internal.shared.errors.exceptions import map_adapter_error, DatabaseError
from kafka_messaging_internal.shared.ports.database_port import DatabasePort, EventRecord, ConsumerOffset


class PostgresAdapter(DatabasePort):
    """PostgreSQL implementation of DatabasePort with tracing and error mapping."""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.dsn = config.get('POSTGRES_DSN')
        self.min_connections = int(config.get('POSTGRES_MIN_CONNECTIONS', '2'))
        self.max_connections = int(config.get('POSTGRES_MAX_CONNECTIONS', '10'))
        self.tracer = trace.get_tracer(__name__)
        
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                dsn=self.dsn
            )
            self._ensure_tables()
        except Exception as e:
            error = map_adapter_error('database', 'connection_failed', e)
            raise error
    
    def _ensure_tables(self):
        """Create necessary tables if they don't exist."""
        with self.tracer.start_as_current_span("postgres.ensure_tables") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "table_creation")
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SET synchronous_commit = off")
                    
                    # Create kafka_events table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS kafka_events (
                            id SERIAL PRIMARY KEY,
                            event_id VARCHAR(255) UNIQUE,
                            topic VARCHAR(255) NOT NULL,
                            partition INTEGER NOT NULL,
                            "offset" BIGINT NOT NULL,
                            key TEXT,
                            value JSONB,
                            timestamp TIMESTAMPTZ NOT NULL,
                            headers JSONB,
                            processed BOOLEAN DEFAULT FALSE,
                            error TEXT,
                            created_at TIMESTAMPTZ DEFAULT NOW(),
                            updated_at TIMESTAMPTZ DEFAULT NOW()
                        )
                    """)
                    
                    # Create indexes
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_kafka_events_unique 
                        ON kafka_events(topic, partition, "offset")
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_events_topic 
                        ON kafka_events(topic)
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_events_topic_created 
                        ON kafka_events(topic, created_at DESC)
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_events_event_id 
                        ON kafka_events(event_id)
                    """)
                    
                    # Create consumer_offsets table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS consumer_offsets (
                            id SERIAL PRIMARY KEY,
                            consumer_group VARCHAR(255) NOT NULL,
                            topic VARCHAR(255) NOT NULL,
                            partition INTEGER NOT NULL,
                            "offset" BIGINT NOT NULL,
                            updated_at TIMESTAMPTZ DEFAULT NOW(),
                            UNIQUE(consumer_group, topic, partition)
                        )
                    """)
                    
                    conn.commit()
            except Exception as e:
                conn.rollback()
                error = map_adapter_error('database', 'query_failed', e)
                span.record_error(error)
                raise error
            finally:
                self._pool.putconn(conn)
    
    async def save_event(self, event: EventRecord) -> str:
        """Save a single event to database."""
        with self.tracer.start_as_current_span("postgres.save_event") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "save_event")
            span.set_attribute("topic", event.topic)
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    query = """
                        INSERT INTO kafka_events 
                        (event_id, topic, partition, "offset", key, value, timestamp, headers)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (event_id) DO UPDATE SET
                        processed = EXCLUDED.processed,
                        error = EXCLUDED.error,
                        updated_at = NOW()
                        RETURNING event_id
                    """
                    cur.execute(
                        query,
                        (
                            getattr(event, 'event_id', None),
                            event.topic,
                            event.partition,
                            event.offset,
                            event.key,
                            json.dumps(event.value) if event.value else None,
                            event.timestamp,
                            json.dumps(event.headers) if event.headers else None
                        )
                    )
                    result = cur.fetchone()
                    conn.commit()
                    return result[0] if result else None
            except Exception as e:
                conn.rollback()
                error = map_adapter_error('database', 'query_failed', e)
                span.record_error(error)
                raise error
            finally:
                self._pool.putconn(conn)
    
    async def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        """Save multiple events in a batch."""
        with self.tracer.start_as_current_span("postgres.save_events_batch") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "save_events_batch")
            span.set_attribute("batch_size", str(len(events)))
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    query = """
                        INSERT INTO kafka_events 
                        (event_id, topic, partition, "offset", key, value, timestamp, headers)
                        VALUES %s
                        ON CONFLICT (event_id) DO UPDATE SET
                        processed = EXCLUDED.processed,
                        error = EXCLUDED.error,
                        updated_at = NOW()
                        RETURNING event_id
                    """
                    values = [
                        (
                            getattr(event, 'event_id', None),
                            event.topic,
                            event.partition,
                            event.offset,
                            event.key,
                            json.dumps(event.value) if event.value else None,
                            event.timestamp,
                            json.dumps(event.headers) if event.headers else None
                        )
                        for event in events
                    ]
                    
                    extras.execute_values(cur, query, values)
                    results = cur.fetchall()
                    conn.commit()
                    return [result[0] for result in results]
            except Exception as e:
                conn.rollback()
                error = map_adapter_error('database', 'query_failed', e)
                span.record_error(error)
                raise error
            finally:
                self._pool.putconn(conn)
    
    async def get_event(self, event_id: str) -> Optional[EventRecord]:
        """Get a single event by ID."""
        with self.tracer.start_as_current_span("postgres.get_event") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "get_event")
            span.set_attribute("event_id", event_id)
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    query = """
                        SELECT event_id, topic, partition, "offset", key, value, timestamp, 
                               headers, processed, error, created_at
                        FROM kafka_events 
                        WHERE event_id = %s
                    """
                    cur.execute(query, (event_id,))
                    result = cur.fetchone()
                    
                    if result:
                        return EventRecord(
                            event_id=result[0],
                            topic=result[1],
                            partition=result[2],
                            offset=result[3],
                            key=result[4],
                            value=result[5] if result[5] else None,
                            timestamp=result[6],
                            headers=result[7] if result[7] else None,
                            processed=result[8],
                            error=result[9],
                            created_at=result[10]
                        )
                    return None
            except Exception as e:
                error = map_adapter_error('database', 'query_failed', e)
                span.record_error(error)
                raise error
            finally:
                self._pool.putconn(conn)
    
    async def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        """Get events by topic with pagination."""
        with self.tracer.start_as_current_span("postgres.get_events_by_topic") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "get_events_by_topic")
            span.set_attribute("topic", topic)
            span.set_attribute("limit", str(limit))
            span.set_attribute("offset", str(offset))
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    query = """
                        SELECT event_id, topic, partition, "offset", key, value, timestamp,
                               headers, processed, error, created_at
                        FROM kafka_events 
                        WHERE topic = %s 
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """
                    cur.execute(query, (topic, limit, offset))
                    results = cur.fetchall()
                    
                    events = []
                    for result in results:
                        events.append(EventRecord(
                            event_id=result[0],
                            topic=result[1],
                            partition=result[2],
                            offset=result[3],
                            key=result[4],
                            value=result[5] if result[5] else None,
                            timestamp=result[6],
                            headers=result[7] if result[7] else None,
                            processed=result[8],
                            error=result[9],
                            created_at=result[10]
                        ))
                    return events
            except Exception as e:
                error = map_adapter_error('database', 'query_failed', e)
                span.record_error(error)
                raise error
            finally:
                self._pool.putconn(conn)
    
    async def get_unprocessed_events(self, limit: int = 100) -> List[EventRecord]:
        """Get unprocessed events."""
        with self.tracer.start_as_current_span("postgres.get_unprocessed_events") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "get_unprocessed_events")
            span.set_attribute("limit", str(limit))
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    query = """
                        SELECT event_id, topic, partition, "offset", key, value, timestamp,
                               headers, processed, error, created_at
                        FROM kafka_events 
                        WHERE processed = FALSE 
                        ORDER BY created_at ASC
                        LIMIT %s
                    """
                    cur.execute(query, (limit,))
                    results = cur.fetchall()
                    
                    events = []
                    for result in results:
                        events.append(EventRecord(
                            event_id=result[0],
                            topic=result[1],
                            partition=result[2],
                            offset=result[3],
                            key=result[4],
                            value=json.loads(result[5]) if result[5] else None,
                            timestamp=result[6],
                            headers=json.loads(result[7]) if result[7] else None,
                            processed=result[8],
                            error=result[9],
                            created_at=result[10]
                        ))
                    return events
            except Exception as e:
                error = map_adapter_error('database', 'query_failed', e)
                span.record_error(error)
                raise error
            finally:
                self._pool.putconn(conn)
    
    async def mark_event_processed(self, event_id: str, error: Optional[str] = None) -> bool:
        """Mark an event as processed."""
        with self.tracer.start_as_current_span("postgres.mark_event_processed") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "mark_event_processed")
            span.set_attribute("event_id", event_id)
            span.set_attribute("has_error", str(error is not None))
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    query = """
                        UPDATE kafka_events 
                        SET processed = TRUE, error = %s, updated_at = NOW()
                        WHERE event_id = %s
                    """
                    cur.execute(query, (error, event_id))
                    conn.commit()
                    return cur.rowcount > 0
            except Exception as e:
                conn.rollback()
                error = map_adapter_error('database', 'query_failed', e)
                span.record_error(error)
                raise error
            finally:
                self._pool.putconn(conn)
    
    async def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        """Save consumer offset."""
        with self.tracer.start_as_current_span("postgres.save_consumer_offset") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "save_consumer_offset")
            span.set_attribute("consumer_group", offset.consumer_group)
            span.set_attribute("topic", offset.topic)
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    query = """
                        INSERT INTO consumer_offsets (consumer_group, topic, partition, "offset")
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (consumer_group, topic, partition) 
                        DO UPDATE SET "offset" = EXCLUDED."offset", updated_at = NOW()
                    """
                    cur.execute(
                        query,
                        (offset.consumer_group, offset.topic, offset.partition, offset.offset)
                    )
                    conn.commit()
                    return True
            except Exception as e:
                conn.rollback()
                error = map_adapter_error('database', 'query_failed', e)
                span.record_error(error)
                raise error
            finally:
                self._pool.putconn(conn)
    
    async def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[ConsumerOffset]:
        """Get consumer offset."""
        with self.tracer.start_as_current_span("postgres.get_consumer_offset") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "get_consumer_offset")
            span.set_attribute("consumer_group", consumer_group)
            span.set_attribute("topic", topic)
            span.set_attribute("partition", str(partition))
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    query = """
                        SELECT consumer_group, topic, partition, "offset", updated_at
                        FROM consumer_offsets 
                        WHERE consumer_group = %s AND topic = %s AND partition = %s
                    """
                    cur.execute(query, (consumer_group, topic, partition))
                    result = cur.fetchone()
                    
                    if result:
                        return ConsumerOffset(
                            consumer_group=result[0],
                            topic=result[1],
                            partition=result[2],
                            offset=result[3],
                            updated_at=result[4]
                        )
                    return None
            except Exception as e:
                error = map_adapter_error('database', 'query_failed', e)
                span.record_error(error)
                raise error
            finally:
                self._pool.putconn(conn)
    
    async def delete_events_by_topic(self, topic: str) -> int:
        """Delete all events for a topic."""
        with self.tracer.start_as_current_span("postgres.delete_events_by_topic") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "delete_events_by_topic")
            span.set_attribute("topic", topic)
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    query = "DELETE FROM kafka_events WHERE topic = %s"
                    cur.execute(query, (topic,))
                    deleted_count = cur.rowcount
                    conn.commit()
                    return deleted_count
            except Exception as e:
                conn.rollback()
                error = map_adapter_error('database', 'query_failed', e)
                span.record_error(error)
                raise error
            finally:
                self._pool.putconn(conn)
    
    async def get_event_count(self, topic: Optional[str] = None) -> int:
        """Get event count."""
        with self.tracer.start_as_current_span("postgres.get_event_count") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "get_event_count")
            span.set_attribute("topic", topic or "all")
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    if topic:
                        query = "SELECT COUNT(*) FROM kafka_events WHERE topic = %s"
                        cur.execute(query, (topic,))
                    else:
                        query = "SELECT COUNT(*) FROM kafka_events"
                        cur.execute(query)
                    
                    result = cur.fetchone()
                    return result[0] if result else 0
            except Exception as e:
                error = map_adapter_error('database', 'query_failed', e)
                span.record_error(error)
                raise error
            finally:
                self._pool.putconn(conn)
    
    async def connect(self) -> None:
        """Establish database connection."""
        with self.tracer.start_as_current_span("postgres.connect") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "connect")
            
            # Connection is already established in __init__
            return None
    
    async def disconnect(self) -> None:
        """Close database connection."""
        with self.tracer.start_as_current_span("postgres.disconnect") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "disconnect")
            
            if self._pool:
                self._pool.closeall()

    async def close(self) -> None:
        """Alias for disconnect to satisfy DatabasePort interface."""
        await self.disconnect()
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        with self.tracer.start_as_current_span("postgres.execute_query") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "query")
            span.set_attribute("query.type", "select")
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    if params:
                        cur.execute(query, params)
                    else:
                        cur.execute(query)
                    
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]
            finally:
                self._pool.putconn(conn)
    
    async def execute_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Execute a command and return affected rows."""
        with self.tracer.start_as_current_span("postgres.execute_command") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "command")
            span.set_attribute("command.type", "insert/update/delete")
            
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    if params:
                        cur.execute(command, params)
                    else:
                        cur.execute(command)
                    
                    conn.commit()
                    return cur.rowcount if hasattr(cur, 'rowcount') else 0
            finally:
                self._pool.putconn(conn)
    
    async def begin_transaction(self) -> None:
        """Begin a transaction."""
        with self.tracer.start_as_current_span("postgres.begin_transaction") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "transaction_begin")
            
            conn = self._pool.getconn()
            try:
                conn.autocommit = False
            finally:
                self._pool.putconn(conn)
    
    async def commit_transaction(self) -> None:
        """Commit a transaction."""
        with self.tracer.start_as_current_span("postgres.commit_transaction") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "transaction_commit")
            
            conn = self._pool.getconn()
            try:
                conn.commit()
                conn.autocommit = True
            finally:
                self._pool.putconn(conn)
    
    async def rollback_transaction(self) -> None:
        """Rollback a transaction."""
        with self.tracer.start_as_current_span("postgres.rollback_transaction") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "transaction_rollback")
            
            conn = self._pool.getconn()
            try:
                conn.rollback()
                conn.autocommit = True
            finally:
                self._pool.putconn(conn)
    
    async def health_check(self) -> bool:
        """Check database health."""
        with self.tracer.start_as_current_span("postgres.health_check") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "health_check")
            
            try:
                conn = self._pool.getconn()
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True
            except Exception:
                return False
            finally:
                try:
                    self._pool.putconn(conn)
                except:
                    pass
    
    
