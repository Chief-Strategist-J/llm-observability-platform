import psycopg
from datetime import datetime
from typing import List, Tuple, Optional
from shared.ports.postgres_port import PostgresPort

class PostgresAdapter(PostgresPort):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def write_forecast(
        self,
        service: str,
        model: str,
        forecast_time: datetime,
        mean: float,
        p10: float,
        p90: float
    ) -> None:
        query = """
        INSERT INTO forecasts (
            service, model, forecast_time, forecast_mean, forecast_p10, forecast_p90, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (service, model, forecast_time) DO UPDATE SET
            forecast_mean = EXCLUDED.forecast_mean,
            forecast_p10 = EXCLUDED.forecast_p10,
            forecast_p90 = EXCLUDED.forecast_p90,
            updated_at = CURRENT_TIMESTAMP
        """
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (service, model, forecast_time, mean, p10, p90))
            conn.commit()

    def get_budget_limits(self) -> List[Tuple[str, str, float]]:
        query = """
        SELECT user_id, model, max_budget FROM budget_configs
        """
        try:
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    rows = cur.fetchall()
                    return [(str(row[0]), str(row[1]), float(row[2])) for row in rows]
        except Exception:
            # Table might not exist or empty in certain test environments
            return []
