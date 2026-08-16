CREATE TABLE IF NOT EXISTS auth_users (
  id VARCHAR(64) PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  org_id VARCHAR(64) NOT NULL,
  org_name VARCHAR(255) NOT NULL,
  role VARCHAR(64) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_auth_users_org_id ON auth_users(org_id);

CREATE TABLE IF NOT EXISTS auth_api_keys (
  key_id VARCHAR(64) PRIMARY KEY,
  org_id VARCHAR(64) NOT NULL,
  key_hash VARCHAR(255) NOT NULL UNIQUE,
  prefix VARCHAR(64) NOT NULL,
  name VARCHAR(255) NOT NULL,
  created_at_ms BIGINT NOT NULL,
  revoked BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_auth_api_keys_hash ON auth_api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_auth_api_keys_org_id ON auth_api_keys(org_id);
