-- migration:      0001
-- description:    rollback initialize job_runs table
-- author:         codex
-- date:           2026-05-14
-- depends_on:     0001
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema only
-- reason:         rollback path for initialization

DROP TABLE IF EXISTS job_runs;
