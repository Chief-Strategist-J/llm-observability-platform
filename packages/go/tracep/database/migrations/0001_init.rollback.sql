-- Rollback Migration: Initialize trace database schema
-- Target: SQLite WAL

DROP INDEX IF EXISTS idx_traces_status;
DROP INDEX IF EXISTS idx_traces_start_time;
DROP INDEX IF EXISTS idx_steps_tid;
DROP INDEX IF EXISTS idx_steps_sid;
DROP INDEX IF EXISTS idx_spans_parent_sid;
DROP INDEX IF EXISTS idx_spans_function;
DROP INDEX IF EXISTS idx_spans_class;
DROP INDEX IF EXISTS idx_spans_tid;

DROP TABLE IF EXISTS steps;
DROP TABLE IF EXISTS spans;
DROP TABLE IF EXISTS traces;
