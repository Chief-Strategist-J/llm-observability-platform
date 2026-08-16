-- Rollback Migration: 0004_add_organization_user_block_soft_delete_cascade.rollback.sql
-- Description: Rollback user blocking columns, permissions array, and soft-delete retention indexes

DROP INDEX IF EXISTS idx_auth_users_blocked;
DROP INDEX IF EXISTS idx_auth_orgs_deleted_at;
DROP INDEX IF EXISTS idx_auth_users_deleted_at;
DROP INDEX IF EXISTS idx_auth_api_keys_deleted_at;
DROP INDEX IF EXISTS idx_auth_audit_logs_deleted_at;
DROP INDEX IF EXISTS idx_auth_resets_deleted_at;

ALTER TABLE auth_users DROP COLUMN IF EXISTS blocked;
ALTER TABLE auth_users DROP COLUMN IF EXISTS blocked_at;
ALTER TABLE auth_users DROP COLUMN IF EXISTS user_permissions;
