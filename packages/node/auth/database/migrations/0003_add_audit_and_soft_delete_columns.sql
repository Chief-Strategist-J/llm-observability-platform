-- migration:      0003
-- description:    add updated_at and deleted_at columns for auditability and soft deletes
-- author:         engineering
-- date:           2026-08-16
-- depends_on:     0002
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema column addition
-- reason:         comply with RULE-04 data normalization policy for auditability and soft-deletes

-- Nullable column reason (per migration.md L203 & data-normalization.md RULE-09):
-- deleted_at is nullable by design because non-deleted active rows carry NULL deleted_at timestamp.

ALTER TABLE auth_organizations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE auth_organizations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

ALTER TABLE auth_users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE auth_users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

ALTER TABLE auth_api_keys ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE auth_api_keys ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

ALTER TABLE auth_audit_logs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE auth_audit_logs ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

ALTER TABLE auth_password_resets ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE auth_password_resets ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
