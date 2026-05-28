import psycopg
from typing import Optional, List
from datetime import datetime
from opentelemetry import trace
from budget_provisioner.shared.ports.db_port import DbPort
from budget_provisioner.features.budget_management.types import BudgetConfig

tracer = trace.get_tracer("budget-provisioner")

class PostgresAdapter(DbPort):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def upsert_budget(
        self,
        user_id: str,
        model: str,
        max_budget: float,
        window_size_secs: int,
        initial_fill_fraction: float
    ) -> BudgetConfig:
        query = """
        INSERT INTO budget_configs (
            user_id, model, max_budget, window_size_secs, initial_fill_fraction, updated_at
        ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id, model) DO UPDATE SET
            max_budget = EXCLUDED.max_budget,
            window_size_secs = EXCLUDED.window_size_secs,
            initial_fill_fraction = EXCLUDED.initial_fill_fraction,
            updated_at = CURRENT_TIMESTAMP
        RETURNING user_id, model, max_budget, window_size_secs, initial_fill_fraction, created_at, updated_at
        """
        with tracer.start_as_current_span(
            "postgres_adapter.upsert_budget",
            attributes={
                "db.system": "postgresql",
                "db.operation": "upsert",
                "db.user_id": user_id,
                "db.model": model
            }
        ) as span:
            try:
                with psycopg.connect(self.dsn) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            query,
                            (
                                user_id,
                                model,
                                max_budget,
                                window_size_secs,
                                initial_fill_fraction
                            )
                        )
                        row = cur.fetchone()
                        conn.commit()
                        if not row:
                            raise RuntimeError("Upsert failed to return a row")
                        return BudgetConfig(
                            user_id=row[0],
                            model=row[1],
                            max_budget=float(row[2]),
                            window_size_secs=int(row[3]),
                            initial_fill_fraction=float(row[4]),
                            created_at=row[5],
                            updated_at=row[6]
                        )
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise

    def get_budget(self, user_id: str, model: str) -> Optional[BudgetConfig]:
        query = """
        SELECT user_id, model, max_budget, window_size_secs, initial_fill_fraction, created_at, updated_at
        FROM budget_configs
        WHERE user_id = %s AND model = %s
        """
        with tracer.start_as_current_span(
            "postgres_adapter.get_budget",
            attributes={
                "db.system": "postgresql",
                "db.operation": "select",
                "db.user_id": user_id,
                "db.model": model
            }
        ) as span:
            try:
                with psycopg.connect(self.dsn) as conn:
                    with conn.cursor() as cur:
                        cur.execute(query, (user_id, model))
                        row = cur.fetchone()
                        if not row:
                            return None
                        return BudgetConfig(
                            user_id=row[0],
                            model=row[1],
                            max_budget=float(row[2]),
                            window_size_secs=int(row[3]),
                            initial_fill_fraction=float(row[4]),
                            created_at=row[5],
                            updated_at=row[6]
                        )
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise

    def list_budgets(self, user_id: str) -> List[BudgetConfig]:
        query = """
        SELECT user_id, model, max_budget, window_size_secs, initial_fill_fraction, created_at, updated_at
        FROM budget_configs
        WHERE user_id = %s
        """
        with tracer.start_as_current_span(
            "postgres_adapter.list_budgets",
            attributes={
                "db.system": "postgresql",
                "db.operation": "select",
                "db.user_id": user_id
            }
        ) as span:
            try:
                with psycopg.connect(self.dsn) as conn:
                    with conn.cursor() as cur:
                        cur.execute(query, (user_id,))
                        rows = cur.fetchall()
                        results = []
                        for row in rows:
                            results.append(
                                BudgetConfig(
                                    user_id=row[0],
                                    model=row[1],
                                    max_budget=float(row[2]),
                                    window_size_secs=int(row[3]),
                                    initial_fill_fraction=float(row[4]),
                                    created_at=row[5],
                                    updated_at=row[6]
                                )
                            )
                        return results
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise

    def delete_budget(self, user_id: str, model: str) -> bool:
        query = """
        DELETE FROM budget_configs
        WHERE user_id = %s AND model = %s
        """
        with tracer.start_as_current_span(
            "postgres_adapter.delete_budget",
            attributes={
                "db.system": "postgresql",
                "db.operation": "delete",
                "db.user_id": user_id,
                "db.model": model
            }
        ) as span:
            try:
                with psycopg.connect(self.dsn) as conn:
                    with conn.cursor() as cur:
                        cur.execute(query, (user_id, model))
                        deleted = cur.rowcount > 0
                        conn.commit()
                        return deleted
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise
