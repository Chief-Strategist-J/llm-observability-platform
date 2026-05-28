import json
import psycopg
from typing import Any
from shared.ports.db_port import DbPort

class PostgresAdapter(DbPort):
    def __init__(self, dsn: str):
        self.dsn = dsn

    def insert_alert(
        self,
        alert_type: str,
        service: str | None,
        model: str | None,
        user_id: str | None,
        event_type: str | None,
        payload: dict[str, Any],
        delivery_latency_ms: int | None
    ) -> None:
        query = """
        INSERT INTO alert_history (
            alert_type, service, model, user_id, event_type, payload, delivery_latency_ms
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        alert_type,
                        service,
                        model,
                        user_id,
                        event_type,
                        json.dumps(payload),
                        delivery_latency_ms
                    )
                )
            conn.commit()
