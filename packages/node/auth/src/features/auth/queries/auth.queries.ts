export const AUTH_QUERIES = {
  FLOW_SIGN_UP: {
    CHECK_ORG_EXISTS: `SELECT id FROM auth_organizations WHERE name = $1 OR slug = $2 LIMIT 1`,
    INSERT_ORG: `INSERT INTO auth_organizations (id, name, slug) VALUES ($1, $2, $3)`,
    INSERT_USER: `INSERT INTO auth_users (id, email, password_hash, name, org_id, org_name, role) VALUES ($1, $2, $3, $4, $5, $6, $7)`,
  },
  FLOW_SIGN_IN: {
    FIND_USER_BY_EMAIL: `SELECT id, email, password_hash, name, org_id, org_name, role FROM auth_users WHERE email = $1 LIMIT 1`,
    RECORD_AUDIT_LOG: `INSERT INTO auth_audit_logs (id, user_id, org_id, event_type, ip_address, user_agent, timestamp_ms) VALUES ($1, $2, $3, $4, $5, $6, $7)`,
  },
  FLOW_SESSION_VERIFY: {
    FIND_USER_BY_ID: `SELECT id, email, password_hash, name, org_id, org_name, role FROM auth_users WHERE id = $1 LIMIT 1`,
  },
  FLOW_FORGOT_PASSWORD: {
    INSERT_RESET_TOKEN: `INSERT INTO auth_password_resets (token_hash, user_id, expires_at_ms, used) VALUES ($1, $2, $3, $4)`,
    FIND_RESET_TOKEN: `SELECT token_hash, user_id, expires_at_ms, used FROM auth_password_resets WHERE token_hash = $1 LIMIT 1`,
  },
  FLOW_RESET_PASSWORD: {
    UPDATE_PASSWORD_HASH: `UPDATE auth_users SET password_hash = $1 WHERE id = $2`,
    MARK_TOKEN_USED: `UPDATE auth_password_resets SET used = TRUE WHERE token_hash = $1`,
  },
  FLOW_CREATE_API_KEY: {
    INSERT_API_KEY: `INSERT INTO auth_api_keys (key_id, org_id, key_type, key_hash, prefix, name, permissions, created_at_ms, revoked) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
  },
  FLOW_VERIFY_API_KEY: {
    FIND_API_KEY_BY_HASH: `SELECT key_id, org_id, key_type, key_hash, prefix, name, permissions, created_at_ms, revoked FROM auth_api_keys WHERE key_hash = $1 LIMIT 1`,
  },
  FLOW_REVOKE_API_KEY: {
    REVOKE_API_KEY_BY_ID: `UPDATE auth_api_keys SET revoked = TRUE WHERE key_id = $1`,
  },
  FLOW_AUDIT_LOGS: {
    FETCH_LOGS_BY_USER: `SELECT id, user_id, org_id, event_type, ip_address, user_agent, timestamp_ms FROM auth_audit_logs WHERE user_id = $1 ORDER BY timestamp_ms DESC LIMIT 100`,
  },
} as const;
