import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone

class SQLiteBackend:
    def __init__(self, db_path: str | None = None) -> None:
        path = db_path or str(Path.home() / ".event-cost" / "ledger.db")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS spans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                span_id TEXT UNIQUE,
                org_id TEXT,
                project_id TEXT,
                service_name TEXT,
                model TEXT,
                provider TEXT,
                user_id TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                cost_usd_micro INTEGER,
                recorded_at TEXT
            );
            CREATE TABLE IF NOT EXISTS budgets (
                org_id TEXT,
                project_id TEXT,
                budget_micro INTEGER,
                spent_micro INTEGER DEFAULT 0,
                PRIMARY KEY (org_id, project_id)
            );
            CREATE INDEX IF NOT EXISTS idx_spans_org_time
                ON spans(org_id, recorded_at);
        """)
        self._conn.commit()

    def record(self, span, cost_usd_micro: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT OR IGNORE INTO spans
            (span_id, org_id, project_id, service_name, model, provider,
             user_id, prompt_tokens, completion_tokens, cost_usd_micro, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), span.org_id, span.project_id,
            span.service_name, span.model, span.provider,
            span.user_id, span.prompt_tokens, span.completion_tokens,
            cost_usd_micro, now,
        ))
        self._conn.execute("""
            INSERT INTO budgets (org_id, project_id, budget_micro, spent_micro)
            VALUES (?, ?, 0, ?)
            ON CONFLICT(org_id, project_id)
            DO UPDATE SET spent_micro = spent_micro + excluded.spent_micro
        """, (span.org_id, span.project_id, cost_usd_micro))
        self._conn.commit()

    def query_total(self, org_id: str, window: str, **filters) -> int:
        window_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
        hours = window_map.get(window, 24)
        modifier = f"-{hours} hours"
        row = self._conn.execute("""
            SELECT COALESCE(SUM(cost_usd_micro), 0)
            FROM spans
            WHERE org_id = ? AND recorded_at >= datetime('now', ?)
        """, (org_id, modifier)).fetchone()
        return row[0] if row else 0

    def get_budget(self, org_id: str, project_id: str) -> int:
        row = self._conn.execute("""
            SELECT budget_micro - spent_micro FROM budgets
            WHERE org_id = ? AND project_id = ?
        """, (org_id, project_id)).fetchone()
        return row[0] if row else 0

    def set_budget(self, org_id: str, project_id: str, micro: int) -> None:
        self._conn.execute("""
            INSERT INTO budgets (org_id, project_id, budget_micro, spent_micro)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(org_id, project_id)
            DO UPDATE SET budget_micro = excluded.budget_micro
        """, (org_id, project_id, micro))
        self._conn.commit()

    def check_anomaly(self, service_name: str, model: str) -> bool:
        return False
