-- Rollback Migration: 0002_add_indexes_on_all_ids_and_keys.rollback.sql
-- Description: Rollback all added ID and key indexes

DROP INDEX IF EXISTS idx_auth_users_id_org_id;
DROP INDEX IF EXISTS idx_auth_api_keys_key_id_org_id;
DROP INDEX IF EXISTS idx_auth_api_keys_prefix;
DROP INDEX IF EXISTS idx_auth_audit_logs_user_org;
DROP INDEX IF EXISTS idx_auth_audit_logs_timestamp;
DROP INDEX IF EXISTS idx_auth_resets_user_expires;
