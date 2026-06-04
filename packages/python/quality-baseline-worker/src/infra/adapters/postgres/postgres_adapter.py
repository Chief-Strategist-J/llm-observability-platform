from typing import List
from datetime import datetime
import psycopg
from shared.ports.postgres_port import PostgresPort
from features.quality_baseline.types import BaselineRecomputeResult, DailyRollupRecord

class PostgresAdapter(PostgresPort):
    def __init__(self, dsn: str):
        self.dsn = dsn

    def get_rolling_baselines(self) -> List[BaselineRecomputeResult]:
        query = """
        SELECT model, endpoint, COALESCE(prompt_type, 'none') as prompt_type, AVG(composite_score), COUNT(*)
        FROM quality_scores
        WHERE scored_at > NOW() - INTERVAL '7 days'
          AND composite_score IS NOT NULL
        GROUP BY model, endpoint, prompt_type
        """
        results = []
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                for row in cur.fetchall():
                    results.append(
                        BaselineRecomputeResult(
                            model=str(row[0]),
                            endpoint=str(row[1]),
                            prompt_type=str(row[2]),
                            avg_score=float(row[3]) if row[3] is not None else 0.0,
                            sample_count=int(row[4]),
                        )
                    )
        return results

    def get_daily_rollup_data(self, start_time: datetime, end_time: datetime) -> List[DailyRollupRecord]:
        query = """
        SELECT model, endpoint, COALESCE(prompt_type, 'none') as prompt_type, 
               AVG(composite_score) as avg_score, 
               COALESCE(SUM(coalesce(cardinality(quality_flags), 0)), 0) as flag_count, 
               COUNT(*) as sample_count
        FROM quality_scores
        WHERE scored_at >= %s AND scored_at <= %s
          AND composite_score IS NOT NULL
        GROUP BY model, endpoint, prompt_type
        """
        results = []
        rollup_date = start_time.date()
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (start_time, end_time))
                for row in cur.fetchall():
                    results.append(
                        DailyRollupRecord(
                            rollup_date=rollup_date,
                            model=str(row[0]),
                            endpoint=str(row[1]),
                            prompt_type=str(row[2]),
                            avg_composite_score=float(row[3]) if row[3] is not None else 0.0,
                            flag_count=int(row[4]),
                            sample_count=int(row[5]),
                        )
                    )
        return results
