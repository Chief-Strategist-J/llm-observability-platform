-- Migration: 0002_add_review_status
-- Description: Add review_status and reviewed_at columns to quality_scores table
-- Rollback: 0002_add_review_status.rollback.sql

ALTER TABLE quality_scores
ADD COLUMN review_status TEXT NOT NULL DEFAULT 'pending',
ADD COLUMN reviewed_at TIMESTAMPTZ NULL;

CREATE INDEX IF NOT EXISTS idx_quality_scores_review_status
ON quality_scores (review_status);
