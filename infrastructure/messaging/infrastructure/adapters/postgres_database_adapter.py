import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import psycopg2
from psycopg2 import pool, extras
from domain.ports.database_port import DatabasePort, EventRecord, ConsumerOffset


class PostgresDatabaseAdapter(DatabasePort):
    def __init__(self, dsn: str, minconn: int = 2, maxconn: int = 10):
        self._pool = psycopg2.pool.ThreadedConnectionPool(minconn=minconn, maxconn=maxconn, dsn=dsn)
        self._ensure_tables()

    def _ensure_tables(self):
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SET synchronous_commit = off")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS kafka_events (
                        id SERIAL PRIMARY KEY,
                        topic VARCHAR(255) NOT NULL,
                        partition INTEGER NOT NULL,
                        "offset" BIGINT NOT NULL,
                        key TEXT,
                        value JSONB,
                        timestamp TIMESTAMPTZ NOT NULL,
                        headers JSONB,
                        processed BOOLEAN DEFAULT FALSE,
                        error TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_kafka_events_unique 
                    ON kafka_events(topic, partition, "offset")
                """)
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
        finally:
            self._pool.putconn(conn)

    def _get_connection(self):
        return self._pool.getconn()

    def _put_connection(self, conn):
        self._pool.putconn(conn)

    def save_event(self, event: EventRecord) -> str:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO kafka_events 
                    (topic, partition, "offset", key, value, timestamp, headers, processed, error, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    event.topic,
                    event.partition,
                    event.offset,
                    event.key,
                    json.dumps(event.value) if event.value else None,
                    event.timestamp,
                    json.dumps(event.headers) if event.headers else None,
                    event.processed,
                    event.error,
                    event.created_at
                ))
                result = cur.fetchone()
                conn.commit()
                return str(result[0])
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._put_connection(conn)

    def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                ids = []
                for event in events:
                    cur.execute("""
                        INSERT INTO kafka_events 
                        (topic, partition, "offset", key, value, timestamp, headers, processed, error, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        event.topic,
                        event.partition,
                        event.offset,
                        event.key,
                        json.dumps(event.value) if event.value else None,
                        event.timestamp,
                        json.dumps(event.headers) if event.headers else None,
                        event.processed,
                        event.error,
                        event.created_at
                    ))
                    result = cur.fetchone()
                    ids.append(str(result[0]))
                conn.commit()
                return ids
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._put_connection(conn)

    def get_event(self, event_id: str) -> Optional[EventRecord]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM kafka_events WHERE id = %s", (event_id,))
                row = cur.fetchone()
                if row:
                    return self._row_to_event(row)
                return None
        finally:
            self._put_connection(conn)

    def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM kafka_events 
                    WHERE topic = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                """, (topic, limit, offset))
                rows = cur.fetchall()
                return [self._row_to_event(row) for row in rows]
        finally:
            self._put_connection(conn)

    def get_unprocessed_events(self, limit: int = 100) -> List[EventRecord]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM kafka_events 
                    WHERE processed = FALSE 
                    ORDER BY created_at ASC 
                    LIMIT %s
                """, (limit,))
                rows = cur.fetchall()
                return [self._row_to_event(row) for row in rows]
        finally:
            self._put_connection(conn)

    def mark_event_processed(self, event_id: str, error: Optional[str] = None) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE kafka_events 
                    SET processed = TRUE, error = %s 
                    WHERE id = %s
                """, (error, event_id))
                conn.commit()
                return cur.rowcount > 0
        finally:
            self._put_connection(conn)

    def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO consumer_offsets 
                    (consumer_group, topic, partition, offset, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (consumer_group, topic, partition) 
                    DO UPDATE SET 
                        offset = EXCLUDED.offset,
                        updated_at = EXCLUDED.updated_at
                """, (
                    offset.consumer_group,
                    offset.topic,
                    offset.partition,
                    offset.offset,
                    offset.updated_at
                ))
                conn.commit()
                return True
        finally:
            self._put_connection(conn)

    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[ConsumerOffset]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM consumer_offsets 
                    WHERE consumer_group = %s AND topic = %s AND partition = %s
                """, (consumer_group, topic, partition))
                row = cur.fetchone()
                if row:
                    return ConsumerOffset(
                        consumer_group=row['consumer_group'],
                        topic=row['topic'],
                        partition=row['partition'],
                        offset=row['offset'],
                        updated_at=row['updated_at']
                    )
                return None
        finally:
            self._put_connection(conn)

    def delete_events_by_topic(self, topic: str) -> int:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM kafka_events WHERE topic = %s", (topic,))
                conn.commit()
                return cur.rowcount
        finally:
            self._put_connection(conn)

    def get_event_count(self, topic: Optional[str] = None) -> int:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                if topic:
                    cur.execute("SELECT COUNT(*) FROM kafka_events WHERE topic = %s", (topic,))
                else:
                    cur.execute("SELECT COUNT(*) FROM kafka_events")
                result = cur.fetchone()
                return result[0] if result else 0
        finally:
            self._put_connection(conn)

    def close(self) -> None:
        if self._pool:
            self._pool.closeall()

    def _row_to_event(self, row: Dict[str, Any]) -> EventRecord:
        return EventRecord(
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
