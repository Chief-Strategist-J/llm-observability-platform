-- migration:      0001
-- description:    initialize job_runs table for queue embedding worker
-- author:         codex
-- date:           2026-05-14
-- depends_on:     0000
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema only
-- reason:         persist queue job run lifecycle with retry metadata

CREATE TABLE IF NOT EXISTS job_runs (
  id BIGSERIAL PRIMARY KEY,
  job_name VARCHAR(255) NOT NULL,
  trace_id VARCHAR(255),
  span_id VARCHAR(255),
  status VARCHAR(32) NOT NULL CHECK (status IN ('queued','processing','completed','failed','retrying')),
  attempts INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 5,
  next_retry_at TIMESTAMPTZ,
  error_message TEXT,
  payload JSONB NOT NULL,
  result JSONB,
  deleted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_runs_status_created_at ON job_runs(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_runs_job_name_status ON job_runs(job_name, status);
