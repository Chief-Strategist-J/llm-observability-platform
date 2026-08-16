-- migration:      0005
-- description:    create token denylist table auth_token_denylist for server-side JWT session revocation
-- author:         engineering
-- date:           2026-08-16
-- depends_on:     0004
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema creation
-- reason:         server-side JWT invalidation on sign-out and organization context switching

CREATE TABLE IF NOT EXISTS auth_token_denylist (
  token_hash VARCHAR(512) PRIMARY KEY,
  expires_at_ms BIGINT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_auth_token_denylist_exp ON auth_token_denylist(expires_at_ms);
