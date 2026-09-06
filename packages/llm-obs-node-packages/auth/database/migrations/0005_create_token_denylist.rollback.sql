-- Rollback Migration: 0005_create_token_denylist.rollback.sql
-- Description: Rollback auth_token_denylist table and expiration index

DROP INDEX IF EXISTS idx_auth_token_denylist_exp;
DROP TABLE IF EXISTS auth_token_denylist;
