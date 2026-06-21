-- migration:      0001
-- description:    rollback create forecasts table
-- author:         Antigravity
-- date:           2026-06-21
-- depends_on:     
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema only
-- reason:         Rollback initial schema creation for forecasts table

DROP TABLE IF EXISTS forecasts;
