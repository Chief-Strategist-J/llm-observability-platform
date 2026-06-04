from __future__ import annotations
import psycopg
from datetime import datetime, timezone, timedelta

from shared.types.quality_score_row import QualityScoreRow
from shared.ports.quality_score_repo_port import QualityScoreRepositoryPort



class PostgresQualityScoreAdapter(QualityScoreRepositoryPort):
    """Concrete PostgreSQL adapter for quality_scores table."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def insert_score(self, row: QualityScoreRow) -> None:
        sql = """
        INSERT INTO quality_scores (
            span_id, trace_id, model, endpoint, prompt_type, response_language,
            composite_score, coherence_score, toxicity_score, faithfulness_score,
            perplexity_score, quality_flags, skipped_reason, scored_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        ON CONFLICT (span_id) DO NOTHING
        """
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    row.span_id,
                    row.trace_id,
                    row.model,
                    row.endpoint,
                    row.prompt_type,
                    row.response_language,
                    row.composite_score,
                    row.coherence_score,
                    row.toxicity_score,
                    row.faithfulness_score,
                    row.perplexity_score,
                    row.quality_flags,
                    row.skipped_reason,
                    row.scored_at,
                ))
            conn.commit()

    def get_window_avg(
        self, model: str, endpoint: str, window_seconds: int = 3600
    ) -> float | None:
        sql = """
        SELECT AVG(composite_score), COUNT(*)
        FROM quality_scores
        WHERE model = %s
          AND endpoint = %s
          AND scored_at > NOW() - INTERVAL '%s seconds'
          AND composite_score IS NOT NULL
        """
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (model, endpoint, window_seconds))
                row = cur.fetchone()
                if row and row[0] is not None and int(row[1]) >= 20:
                    return float(row[0])
        return None
