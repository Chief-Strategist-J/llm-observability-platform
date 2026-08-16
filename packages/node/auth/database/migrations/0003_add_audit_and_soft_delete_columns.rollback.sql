-- Rollback Migration: 0003_add_audit_and_soft_delete_columns.rollback.sql
-- Description: Rollback updated_at and deleted_at columns

ALTER TABLE auth_organizations DROP COLUMN IF EXISTS updated_at;
ALTER TABLE auth_organizations DROP COLUMN IF EXISTS deleted_at;

ALTER TABLE auth_users DROP COLUMN IF EXISTS updated_at;
ALTER TABLE auth_users DROP COLUMN IF EXISTS deleted_at;

ALTER TABLE auth_api_keys DROP COLUMN IF EXISTS updated_at;
ALTER TABLE auth_api_keys DROP COLUMN IF EXISTS deleted_at;

ALTER TABLE auth_audit_logs DROP COLUMN IF EXISTS updated_at;
ALTER TABLE auth_audit_logs DROP COLUMN IF EXISTS deleted_at;

ALTER TABLE auth_password_resets DROP COLUMN IF EXISTS updated_at;
ALTER TABLE auth_password_resets DROP COLUMN IF EXISTS deleted_at;
