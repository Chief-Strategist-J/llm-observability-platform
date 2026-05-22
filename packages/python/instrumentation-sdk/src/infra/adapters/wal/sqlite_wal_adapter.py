import sqlite3
from typing import List, Tuple
from src.shared.ports.wal import WalStoragePort

class SqliteWalStorageAdapter(WalStoragePort):
    def __init__(self, wal_path: str) -> None:
        self.wal_path = wal_path

    def initialize(self) -> None:
        with sqlite3.connect(self.wal_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS spans ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "span_id TEXT, "
                "span_json TEXT"
                ")"
            )
            conn.commit()

    def save(self, span_id: str, span_json: str) -> None:
        with sqlite3.connect(self.wal_path) as conn:
            conn.execute(
                "INSERT INTO spans (span_id, span_json) VALUES (?, ?)",
                (span_id, span_json)
            )
            conn.commit()

    def fetch_batch(self, limit: int) -> List[Tuple[int, str, str]]:
        with sqlite3.connect(self.wal_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, span_id, span_json FROM spans ORDER BY id ASC LIMIT ?",
                (limit,)
            )
            return cursor.fetchall()

    def delete_batch(self, ids: List[int]) -> None:
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        with sqlite3.connect(self.wal_path) as conn:
            conn.execute(
                f"DELETE FROM spans WHERE id IN ({placeholders})",
                tuple(ids)
            )
            conn.commit()
