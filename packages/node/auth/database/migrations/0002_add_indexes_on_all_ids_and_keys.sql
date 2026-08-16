-- Migration: 0002_add_indexes_on_all_ids_and_keys.sql
-- Description: Add high-performance B-tree indexes for all primary/foreign IDs and lookup keys

CREATE INDEX IF NOT EXISTS idx_auth_users_id_org_id ON auth_users(id, org_id);
CREATE INDEX IF NOT EXISTS idx_auth_api_keys_key_id_org_id ON auth_api_keys(key_id, org_id);
CREATE INDEX IF NOT EXISTS idx_auth_api_keys_prefix ON auth_api_keys(prefix);
CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_user_org ON auth_audit_logs(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_timestamp ON auth_audit_logs(timestamp_ms DESC);
CREATE INDEX IF NOT EXISTS idx_auth_resets_user_expires ON auth_password_resets(user_id, expires_at_ms);
