-- migration:      0001
-- description:    create auth tables for multi-tenant organizations users api keys audit logs password resets
-- author:         engineering
-- date:           2026-08-16
-- depends_on:     none
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema only
-- reason:         initial schema setup for multi-tenant auth module

CREATE TABLE IF NOT EXISTS auth_organizations (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  slug VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_auth_orgs_name ON auth_organizations(name);
CREATE INDEX IF NOT EXISTS idx_auth_orgs_slug ON auth_organizations(slug);

CREATE TABLE IF NOT EXISTS auth_users (
  id VARCHAR(64) PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  org_id VARCHAR(64) NOT NULL REFERENCES auth_organizations(id),
  org_name VARCHAR(255) NOT NULL,
  role VARCHAR(64) NOT NULL DEFAULT 'member',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_auth_users_org_id ON auth_users(org_id);

ALTER TABLE auth_users ENABLE ROW LEVEL SECURITY;
CREATE POLICY rls_auth_users_tenant_isolation ON auth_users
  FOR ALL
  USING (org_id = current_setting('app.current_org_id', true));

CREATE TABLE IF NOT EXISTS auth_api_keys (
  key_id VARCHAR(64) PRIMARY KEY,
  org_id VARCHAR(64) NOT NULL REFERENCES auth_organizations(id),
  key_type VARCHAR(32) NOT NULL DEFAULT 'general',
  key_hash VARCHAR(255) NOT NULL UNIQUE,
  prefix VARCHAR(64) NOT NULL,
  name VARCHAR(255) NOT NULL,
  permissions TEXT[] NOT NULL,
  created_at_ms BIGINT NOT NULL,
  revoked BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_auth_api_keys_hash ON auth_api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_auth_api_keys_org_id ON auth_api_keys(org_id);
CREATE INDEX IF NOT EXISTS idx_auth_api_keys_type ON auth_api_keys(key_type);

CREATE TABLE IF NOT EXISTS auth_audit_logs (
  id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  org_id VARCHAR(64) NOT NULL,
  event_type VARCHAR(64) NOT NULL,
  ip_address VARCHAR(64) NOT NULL,
  user_agent VARCHAR(512) NOT NULL,
  timestamp_ms BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_user ON auth_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_org ON auth_audit_logs(org_id);

CREATE TABLE IF NOT EXISTS auth_password_resets (
  token_hash VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  expires_at_ms BIGINT NOT NULL,
  used BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_auth_resets_user ON auth_password_resets(user_id);
