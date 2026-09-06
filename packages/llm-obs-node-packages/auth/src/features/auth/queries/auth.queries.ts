export const AUTH_QUERIES = {
  TENANT_RLS: {
    SET_LOCAL_TENANT_CONTEXT: `SELECT set_config('app.current_org_id', $1, true)`,
  },
  FLOW_CREATE_ORGANIZATION: {
    CHECK_ORG_NAME: `SELECT id FROM auth_organizations WHERE name = $1 AND deleted_at IS NULL LIMIT 1`,
    INSERT_ORG: `INSERT INTO auth_organizations (id, name, slug) VALUES ($1, $2, $3)`,
    INSERT_USER_ORG: `INSERT INTO auth_user_organizations (user_id, org_id, role) VALUES ($1, $2, $3) ON CONFLICT (user_id, org_id) DO NOTHING`,
    LIST_BY_USER: `SELECT DISTINCT o.id, o.name, o.slug FROM auth_organizations o LEFT JOIN auth_user_organizations uo ON uo.org_id = o.id LEFT JOIN auth_users u ON u.org_id = o.id WHERE (uo.user_id = $1 OR u.id = $1) AND o.deleted_at IS NULL`,
    GET_BY_ID: `SELECT id, name, slug FROM auth_organizations WHERE id = $1 AND deleted_at IS NULL LIMIT 1`,
    UPDATE_NAME: `UPDATE auth_organizations SET name = $1 WHERE id = $2 AND deleted_at IS NULL`,
    UPDATE_SLUG: `UPDATE auth_organizations SET slug = $1 WHERE id = $2 AND deleted_at IS NULL`,
  },
  FLOW_DELETE_ORGANIZATION: {
    SOFT_DELETE_ORG: `UPDATE auth_organizations SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND deleted_at IS NULL`,
    CASCADE_SOFT_DELETE_USERS: `UPDATE auth_users SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE org_id = $1 AND deleted_at IS NULL`,
    CASCADE_SOFT_DELETE_KEYS: `UPDATE auth_api_keys SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE org_id = $1 AND deleted_at IS NULL`,
    CASCADE_SOFT_DELETE_LOGS: `UPDATE auth_audit_logs SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE org_id = $1 AND deleted_at IS NULL`,
  },
  FLOW_CREATE_USER: {
    FIND_ORG_BY_ID: `SELECT id, name FROM auth_organizations WHERE id = $1 AND deleted_at IS NULL LIMIT 1`,
    INSERT_USER: `INSERT INTO auth_users (id, email, password_hash, name, org_id, org_name, role, user_permissions) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
    INSERT_USER_ORG: `INSERT INTO auth_user_organizations (user_id, org_id, role) VALUES ($1, $2, $3) ON CONFLICT (user_id, org_id) DO NOTHING`,
    LIST_BY_ORG: `SELECT id, email, password_hash, name, org_id, org_name, role, blocked, user_permissions FROM auth_users WHERE org_id = $1 AND deleted_at IS NULL`,
    UNBLOCK_USER: `UPDATE auth_users SET blocked = FALSE, blocked_at = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND deleted_at IS NULL`,
    UPDATE_PROFILE_NAME: `UPDATE auth_users SET name = $1 WHERE id = $2 AND deleted_at IS NULL`,
    UPDATE_ROLE: `UPDATE auth_users SET role = $1 WHERE id = $2 AND deleted_at IS NULL`,
    UPDATE_PERMISSIONS: `UPDATE auth_users SET user_permissions = $1 WHERE id = $2 AND deleted_at IS NULL`,
  },
  FLOW_BLOCK_USER: {
    BLOCK_USER: `UPDATE auth_users SET blocked = TRUE, blocked_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND deleted_at IS NULL`,
  },
  FLOW_DELETE_USER: {
    SOFT_DELETE_USER: `UPDATE auth_users SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND deleted_at IS NULL`,
  },
  FLOW_RETENTION_PURGE: {
    PURGE_ORGS: `DELETE FROM auth_organizations WHERE deleted_at < NOW() - INTERVAL '30 days'`,
    PURGE_USERS: `DELETE FROM auth_users WHERE deleted_at < NOW() - INTERVAL '30 days'`,
    PURGE_KEYS: `DELETE FROM auth_api_keys WHERE deleted_at < NOW() - INTERVAL '30 days'`,
    PURGE_LOGS: `DELETE FROM auth_audit_logs WHERE deleted_at < NOW() - INTERVAL '30 days'`,
    PURGE_RESETS: `DELETE FROM auth_password_resets WHERE deleted_at < NOW() - INTERVAL '30 days'`,
    PURGE_DENYLIST: `DELETE FROM auth_token_denylist WHERE expires_at_ms < $1`,
  },
  FLOW_SIGN_UP: {
    CHECK_ORG_EXISTS: `SELECT id FROM auth_organizations WHERE (name = $1 OR slug = $2) AND deleted_at IS NULL LIMIT 1`,
    INSERT_ORG: `INSERT INTO auth_organizations (id, name, slug) VALUES ($1, $2, $3)`,
    INSERT_USER: `INSERT INTO auth_users (id, email, password_hash, name, org_id, org_name, role, user_permissions) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
    INSERT_USER_ORG: `INSERT INTO auth_user_organizations (user_id, org_id, role) VALUES ($1, $2, $3) ON CONFLICT (user_id, org_id) DO NOTHING`,
  },
  FLOW_SIGN_IN: {
    FIND_USER_BY_EMAIL: `SELECT id, email, password_hash, name, org_id, org_name, role, blocked, user_permissions FROM auth_users WHERE email = $1 AND deleted_at IS NULL LIMIT 1`,
    RECORD_AUDIT_LOG: `INSERT INTO auth_audit_logs (id, user_id, org_id, event_type, ip_address, user_agent, timestamp_ms) VALUES ($1, $2, $3, $4, $5, $6, $7)`,
  },
  FLOW_SESSION_VERIFY: {
    FIND_USER_BY_ID: `SELECT id, email, password_hash, name, org_id, org_name, role, blocked, user_permissions FROM auth_users WHERE id = $1 AND deleted_at IS NULL LIMIT 1`,
    ADD_TOKEN_DENYLIST: `INSERT INTO auth_token_denylist (token_hash, expires_at_ms) VALUES ($1, $2) ON CONFLICT DO NOTHING`,
    CHECK_TOKEN_DENYLIST: `SELECT 1 FROM auth_token_denylist WHERE token_hash = $1 AND expires_at_ms > $2 LIMIT 1`,
  },
  FLOW_FORGOT_PASSWORD: {
    INSERT_RESET_TOKEN: `INSERT INTO auth_password_resets (token_hash, user_id, expires_at_ms, used) VALUES ($1, $2, $3, $4)`,
    FIND_RESET_TOKEN: `SELECT token_hash, user_id, expires_at_ms, used FROM auth_password_resets WHERE token_hash = $1 AND deleted_at IS NULL LIMIT 1`,
  },
  FLOW_RESET_PASSWORD: {
    UPDATE_PASSWORD_HASH: `UPDATE auth_users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 AND deleted_at IS NULL`,
    MARK_TOKEN_USED: `UPDATE auth_password_resets SET used = TRUE, updated_at = CURRENT_TIMESTAMP WHERE token_hash = $1 AND deleted_at IS NULL`,
  },
  FLOW_CREATE_API_KEY: {
    INSERT_API_KEY: `INSERT INTO auth_api_keys (key_id, org_id, key_type, key_hash, prefix, name, permissions, created_at_ms, revoked) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
    LIST_BY_ORG: `SELECT key_id, org_id, key_type, key_hash, prefix, name, permissions, created_at_ms, revoked FROM auth_api_keys WHERE org_id = $1 AND deleted_at IS NULL`,
  },
  FLOW_VERIFY_API_KEY: {
    FIND_API_KEY_BY_HASH: `SELECT key_id, org_id, key_type, key_hash, prefix, name, permissions, created_at_ms, revoked FROM auth_api_keys WHERE key_hash = $1 AND deleted_at IS NULL LIMIT 1`,
  },
  FLOW_REVOKE_API_KEY: {
    REVOKE_API_KEY_BY_ID: `UPDATE auth_api_keys SET revoked = TRUE, updated_at = CURRENT_TIMESTAMP WHERE key_id = $1 AND deleted_at IS NULL`,
  },
  FLOW_AUDIT_LOGS: {
    FETCH_LOGS_BY_USER: `SELECT id, user_id, org_id, event_type, ip_address, user_agent, timestamp_ms FROM auth_audit_logs WHERE user_id = $1 AND deleted_at IS NULL ORDER BY timestamp_ms DESC LIMIT 100`,
  },
} as const;
