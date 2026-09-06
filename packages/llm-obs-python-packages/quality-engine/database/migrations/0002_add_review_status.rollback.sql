-- Rollback: 0002_add_review_status

DROP INDEX IF EXISTS idx_quality_scores_review_status;

ALTER TABLE quality_scores
DROP COLUMN IF EXISTS review_status,
DROP COLUMN IF EXISTS reviewed_at;
