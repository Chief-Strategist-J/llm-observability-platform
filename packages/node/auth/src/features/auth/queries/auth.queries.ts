export const AUTH_QUERIES = {
  FLOW_SIGN_IN: {
    FIND_USER_BY_EMAIL: `SELECT id, email, password_hash, name, org_id, org_name, role FROM auth_users WHERE email = $1 LIMIT 1`,
  },
  FLOW_SESSION_VERIFY: {
    FIND_USER_BY_ID: `SELECT id, email, password_hash, name, org_id, org_name, role FROM auth_users WHERE id = $1 LIMIT 1`,
  },
  FLOW_CREATE_API_KEY: {
    INSERT_API_KEY: `INSERT INTO auth_api_keys (key_id, org_id, key_hash, prefix, name, created_at_ms, revoked) VALUES ($1, $2, $3, $4, $5, $6, $7)`,
  },
  FLOW_VERIFY_API_KEY: {
    FIND_API_KEY_BY_HASH: `SELECT key_id, org_id, key_hash, prefix, name, created_at_ms, revoked FROM auth_api_keys WHERE key_hash = $1 LIMIT 1`,
  },
  FLOW_REVOKE_API_KEY: {
    REVOKE_API_KEY_BY_ID: `UPDATE auth_api_keys SET revoked = TRUE WHERE key_id = $1`,
  },
} as const;
