import os
import sqlite3
from typing import List, Dict, Any

class SQLiteStore:
    def __init__(self, db_path: str = "pytrace.db") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path) if db_path == ":memory:" else None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    start_time_ns INTEGER,
                    end_time_ns INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS spans (
                    span_id TEXT PRIMARY KEY,
                    trace_id TEXT,
                    parent_span_id TEXT,
                    name TEXT,
                    start_time_ns INTEGER,
                    end_time_ns INTEGER,
                    duration_ns INTEGER,
                    service_name TEXT,
                    FOREIGN KEY(trace_id) REFERENCES traces(trace_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    span_id TEXT,
                    type TEXT,
                    tid INTEGER,
                    timestamp_ns INTEGER,
                    name TEXT,
                    duration_ns INTEGER,
                    metadata TEXT,
                    FOREIGN KEY(span_id) REFERENCES spans(span_id)
                )
            """)
            conn.commit()

    def insert_trace(self, trace_id: str, start_time_ns: int, end_time_ns: int) -> None:
        conn = self._get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO traces (trace_id, start_time_ns, end_time_ns) VALUES (?, ?, ?)",
            (trace_id, start_time_ns, end_time_ns)
        )
        conn.commit()

    def insert_span(self, span_id: str, trace_id: str, parent_span_id: str | None, name: str, start_time_ns: int, end_time_ns: int, duration_ns: int, service_name: str) -> None:
        conn = self._get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO spans (span_id, trace_id, parent_span_id, name, start_time_ns, end_time_ns, duration_ns, service_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (span_id, trace_id, parent_span_id, name, start_time_ns, end_time_ns, duration_ns, service_name)
        )
        conn.commit()

    def insert_event(self, span_id: str, event_type: str, tid: int, timestamp_ns: int, name: str, duration_ns: int, metadata: str) -> None:
        conn = self._get_connection()
        conn.execute(
            "INSERT INTO events (span_id, type, tid, timestamp_ns, name, duration_ns, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (span_id, event_type, tid, timestamp_ns, name, duration_ns, metadata)
        )
        conn.commit()

    def get_last_trace_spans(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Fetch last trace
        cursor.execute("SELECT trace_id FROM traces ORDER BY start_time_ns DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            return []
        trace_id = row["trace_id"]
        cursor.execute("SELECT * FROM spans WHERE trace_id = ? ORDER BY start_time_ns ASC", (trace_id,))
        return [dict(r) for r in cursor.fetchall()]

    def get_all_traces_grouped(self) -> Dict[str, List[Dict[str, Any]]]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM spans ORDER BY start_time_ns ASC")
        spans = cursor.fetchall()
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for s in spans:
            tid = s["trace_id"]
            if tid not in grouped:
                grouped[tid] = []
            grouped[tid].append(dict(s))
        return grouped

    def get_slow_paths(self, threshold_ns: int) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM spans WHERE duration_ns >= ? ORDER BY duration_ns DESC", (threshold_ns,))
        return [dict(r) for r in cursor.fetchall()]
