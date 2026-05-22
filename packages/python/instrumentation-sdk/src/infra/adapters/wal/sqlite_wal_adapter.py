import sqlite3
import threading
from typing import List, Tuple, Any
from src.shared.ports.wal import WalStoragePort

class SqliteWalStorageAdapter(WalStoragePort):
    def __init__(self, wal_path: str) -> None:
        self.wal_path = wal_path
        self._lock = threading.Lock()
        self._conn = None

    def initialize(self) -> None:
        self._conn = sqlite3.connect(self.wal_path, check_same_thread=False)
        with self._lock:
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA synchronous = OFF")
            self._conn.execute("PRAGMA temp_store = MEMORY")
            self._conn.execute("PRAGMA cache_size = -20000")
            self._conn.execute("PRAGMA locking_mode = EXCLUSIVE")
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS spans ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "span_id TEXT, "
                "span_json BLOB"
                ")"
            )
            self._conn.commit()

    def save(self, span_id: str, span_json: Any) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO spans (span_id, span_json) VALUES (?, ?)",
                (span_id, span_json)
            )
            self._conn.commit()

    def save_batch(self, spans: List[Tuple[str, Any]]) -> None:
        if not spans:
            return
        with self._lock:
            self._conn.executemany(
                "INSERT INTO spans (span_id, span_json) VALUES (?, ?)",
                spans
            )
            self._conn.commit()

    def fetch_batch(self, limit: int) -> List[Tuple[int, str, Any]]:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id, span_id, span_json FROM spans ORDER BY id ASC LIMIT ?",
                (limit,)
            )
            return cursor.fetchall()

    def delete_batch(self, ids: List[int]) -> None:
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        with self._lock:
            self._conn.execute(
                f"DELETE FROM spans WHERE id IN ({placeholders})",
                tuple(ids)
            )
            self._conn.commit()

