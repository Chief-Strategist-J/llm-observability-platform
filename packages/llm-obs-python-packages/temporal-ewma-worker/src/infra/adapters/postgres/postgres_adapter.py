import psycopg
from shared.ports.postgres_port import PostgresPort
from shared.types.ewma_types import EwmaRecord


class PostgresAdapter(PostgresPort):
    def __init__(self, dsn: str):
        self.dsn = dsn

    def get_baseline(
        self, service: str, model: str, hour_of_week: int
    ) -> EwmaRecord | None:
        query = """
        SELECT service, model, hour_of_week, ewma_value, sample_count, is_cold_start, updated_at
        FROM ewma_baselines
        WHERE service = %s AND model = %s AND hour_of_week = %s
        """
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (service, model, hour_of_week))
                row = cur.fetchone()
                if row:
                    return EwmaRecord(
                        service=row[0],
                        model=row[1],
                        hour_of_week=row[2],
                        ewma_value=float(row[3]),
                        sample_count=int(row[4]),
                        is_cold_start=bool(row[5]),
                        updated_at=row[6],
                    )
        return None

    def upsert_baseline(self, record: EwmaRecord) -> None:
        query = """
        INSERT INTO ewma_baselines (service, model, hour_of_week, ewma_value, sample_count, is_cold_start, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (service, model, hour_of_week)
        DO UPDATE SET
            ewma_value = EXCLUDED.ewma_value,
            sample_count = EXCLUDED.sample_count,
            is_cold_start = EXCLUDED.is_cold_start,
            updated_at = CURRENT_TIMESTAMP
        """
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        record.service,
                        record.model,
                        record.hour_of_week,
                        record.ewma_value,
                        record.sample_count,
                        record.is_cold_start,
                    ),
                )
            conn.commit()
