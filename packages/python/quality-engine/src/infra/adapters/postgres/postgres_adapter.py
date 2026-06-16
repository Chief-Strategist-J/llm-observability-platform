from __future__ import annotations
import json
from datetime import datetime
import psycopg

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
            perplexity_score, quality_flags, skipped_reason, weights_used, scored_at,
            review_status, reviewed_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s
        )
        ON CONFLICT (span_id) DO NOTHING
        """
        weights_json = json.dumps(row.weights_used) if row.weights_used is not None else None
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
                    weights_json,
                    row.scored_at,
                    row.review_status,
                    row.reviewed_at,
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

    def get_review_queue(self, status: str) -> list[QualityScoreRow]:
        sql = """
        SELECT span_id, trace_id, model, endpoint, prompt_type, response_language,
               composite_score, coherence_score, toxicity_score, faithfulness_score,
               perplexity_score, quality_flags, skipped_reason, weights_used, scored_at,
               review_status, reviewed_at
        FROM quality_scores
        WHERE review_status = %s
        ORDER BY scored_at DESC
        """
        results = []
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (status,))
                rows = cur.fetchall()
                for row in rows:
                    weights_used = None
                    if row[13]:
                        if isinstance(row[13], dict):
                            weights_used = row[13]
                        else:
                            weights_used = json.loads(row[13])
                    results.append(QualityScoreRow(
                        span_id=row[0],
                        trace_id=row[1],
                        model=row[2],
                        endpoint=row[3],
                        prompt_type=row[4],
                        response_language=row[5],
                        composite_score=row[6],
                        coherence_score=row[7],
                        toxicity_score=row[8],
                        faithfulness_score=row[9],
                        perplexity_score=row[10],
                        quality_flags=row[11] or [],
                        skipped_reason=row[12],
                        weights_used=weights_used,
                        scored_at=row[14],
                        review_status=row[15],
                        reviewed_at=row[16],
                    ))
        return results

    def update_review_status(self, span_id: str, status: str, reviewed_at: datetime) -> bool:
        sql = """
        UPDATE quality_scores
        SET review_status = %s, reviewed_at = %s
        WHERE span_id = %s
        """
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (status, reviewed_at, span_id))
                rowcount = cur.rowcount
            conn.commit()
        return rowcount > 0
