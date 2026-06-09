-- Migration: 0001_init_quality_scores
-- Description: Create quality_scores table for all scoring results produced by quality-engine
-- Rollback: 0001_init.rollback.sql

CREATE TABLE IF NOT EXISTS quality_scores (
    id                  BIGSERIAL PRIMARY KEY,
    span_id             TEXT        NOT NULL UNIQUE,
    trace_id            TEXT        NOT NULL,
    model               TEXT        NOT NULL,
    endpoint            TEXT        NOT NULL,
    prompt_type         TEXT        NOT NULL DEFAULT 'chat',
    response_language   TEXT        NOT NULL DEFAULT 'en',
    composite_score     FLOAT       NULL,
    coherence_score     FLOAT       NULL,
    toxicity_score      FLOAT       NULL,
    faithfulness_score  FLOAT       NULL,
    perplexity_score    FLOAT       NULL,
    quality_flags       TEXT[]      NOT NULL DEFAULT '{}',
    skipped_reason      TEXT        NULL,
    weights_used        JSONB       NULL,
    scored_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quality_scores_model_endpoint
    ON quality_scores (model, endpoint, scored_at DESC);

CREATE INDEX IF NOT EXISTS idx_quality_scores_scored_at
    ON quality_scores (scored_at DESC);

CREATE INDEX IF NOT EXISTS idx_quality_scores_span_id
    ON quality_scores (span_id);
