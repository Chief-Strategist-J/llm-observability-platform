-- migration:      0004
-- description:    add user blocking columns user_permissions array and indexes for 30-day retention soft-delete purging
-- author:         engineering
-- date:           2026-08-16
-- depends_on:     0003
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema alteration
-- reason:         support user blocking, custom permissions, and 30-day soft delete retention lifecycle

ALTER TABLE auth_users ADD COLUMN IF NOT EXISTS blocked BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE auth_users ADD COLUMN IF NOT EXISTS blocked_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
ALTER TABLE auth_users ADD COLUMN IF NOT EXISTS user_permissions TEXT[] NOT NULL DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_auth_users_blocked ON auth_users(blocked);
CREATE INDEX IF NOT EXISTS idx_auth_orgs_deleted_at ON auth_organizations(deleted_at);
CREATE INDEX IF NOT EXISTS idx_auth_users_deleted_at ON auth_users(deleted_at);
CREATE INDEX IF NOT EXISTS idx_auth_api_keys_deleted_at ON auth_api_keys(deleted_at);
CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_deleted_at ON auth_audit_logs(deleted_at);
CREATE INDEX IF NOT EXISTS idx_auth_resets_deleted_at ON auth_password_resets(deleted_at);
