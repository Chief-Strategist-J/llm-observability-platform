import { Pool } from 'pg';
import { SpanKind } from '@opentelemetry/api';
import type { AuthRepositoryPort, OrganizationRecord } from '../../../features/auth/repository';
import type { AuthUserRecord, AuditLogRecord } from '../../../features/auth/types';
import type { ApiKeyRecord } from '../../../shared/types/auth.types';
import { AUTH_QUERIES } from '../../../features/auth/queries/auth.queries';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';
import { withSpan } from '../../tracing/tracer';

export class RealPostgresAuthAdapter implements AuthRepositoryPort {
  private readonly pool: Pool;
  public readonly queries = AUTH_QUERIES;

  constructor(connectionString?: string) {
    this.pool = new Pool({
      connectionString: connectionString ?? process.env.DATABASE_URL,
      host: process.env.ALLOYDB_OMNI_HOST ?? 'localhost',
      port: process.env.ALLOYDB_OMNI_PORT ? parseInt(process.env.ALLOYDB_OMNI_PORT, 10) : 5432,
      user: process.env.ALLOYDB_OMNI_USER ?? 'postgres',
      password: process.env.ALLOYDB_OMNI_PASSWORD ?? 'postgres',
      database: process.env.ALLOYDB_OMNI_DB ?? 'observability_auth',
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 5000,
    });
    this.pool.on('error', (err: any) => {
      if (err?.code !== '57P01' && !err?.message?.includes('terminating connection')) {
        console.error('[PostgreSQL Pool Error]', err);
      }
    });
  }

  public async getPoolStatus(): Promise<{ totalCount: number; idleCount: number; waitingCount: number }> {
    return {
      totalCount: this.pool.totalCount,
      idleCount: this.pool.idleCount,
      waitingCount: this.pool.waitingCount,
    };
  }

  public async close(): Promise<void> {
    await this.pool.end();
  }

  private async setTenantRlsContext(client: any, orgId: string): Promise<void> {
    await client.query(AUTH_QUERIES.TENANT_RLS.SET_LOCAL_TENANT_CONTEXT, [orgId]);
  }

  async createOrganization(org: OrganizationRecord, creatorUserId?: string): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      const check = await client.query(AUTH_QUERIES.FLOW_CREATE_ORGANIZATION.CHECK_ORG_NAME, [org.name]);
      if (check.rows.length > 0) {
        throw new Error(`Organization name already exists: ${org.name}`);
      }
      await client.query(AUTH_QUERIES.FLOW_CREATE_ORGANIZATION.INSERT_ORG, [org.id, org.name, org.slug]);
      if (creatorUserId) {
        await client.query(AUTH_QUERIES.FLOW_CREATE_ORGANIZATION.INSERT_USER_ORG, [creatorUserId, org.id, AUTH_CONSTANTS.ROLE_ADMIN]);
      }
      await client.query('COMMIT');
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  }

  async listOrganizationsByUserId(userId: string): Promise<OrganizationRecord[]> {
    const client = await this.pool.connect();
    try {
      const res = await client.query(AUTH_QUERIES.FLOW_CREATE_ORGANIZATION.LIST_BY_USER, [userId]);
      return res.rows.map((row: any) => ({ id: row.id, name: row.name, slug: row.slug }));
    } finally {
      client.release();
    }
  }

  async getOrganizationById(orgId: string): Promise<OrganizationRecord | null> {
    const client = await this.pool.connect();
    try {
      const res = await client.query(AUTH_QUERIES.FLOW_CREATE_ORGANIZATION.GET_BY_ID, [orgId]);
      if (res.rows.length === 0) return null;
      const row = res.rows[0];
      return { id: row.id, name: row.name, slug: row.slug };
    } finally {
      client.release();
    }
  }

  async updateOrganization(orgId: string, patch: { name?: string; slug?: string }): Promise<void> {
    const client = await this.pool.connect();
    try {
      if (patch.name) await client.query(AUTH_QUERIES.FLOW_CREATE_ORGANIZATION.UPDATE_NAME, [patch.name, orgId]);
      if (patch.slug) await client.query(AUTH_QUERIES.FLOW_CREATE_ORGANIZATION.UPDATE_SLUG, [patch.slug, orgId]);
    } finally {
      client.release();
    }
  }

  async deleteOrganization(orgId: string): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      await client.query(AUTH_QUERIES.FLOW_DELETE_ORGANIZATION.SOFT_DELETE_ORG, [orgId]);
      await client.query(AUTH_QUERIES.FLOW_DELETE_ORGANIZATION.CASCADE_SOFT_DELETE_USERS, [orgId]);
      await client.query(AUTH_QUERIES.FLOW_DELETE_ORGANIZATION.CASCADE_SOFT_DELETE_KEYS, [orgId]);
      await client.query(AUTH_QUERIES.FLOW_DELETE_ORGANIZATION.CASCADE_SOFT_DELETE_LOGS, [orgId]);
      await client.query('COMMIT');
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  }

  async createUser(userRecord: AuthUserRecord): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      const orgCheck = await client.query(AUTH_QUERIES.FLOW_CREATE_USER.FIND_ORG_BY_ID, [userRecord.org_id]);
      if (orgCheck.rows.length === 0) {
        throw new Error(`Organization ${userRecord.org_id} does not exist or has been deleted`);
      }
      const orgName = orgCheck.rows[0].name;
      await this.setTenantRlsContext(client, userRecord.org_id);
      await client.query(AUTH_QUERIES.FLOW_CREATE_USER.INSERT_USER, [
        userRecord.id,
        userRecord.email,
        userRecord.password_hash,
        userRecord.name,
        userRecord.org_id,
        orgName,
        userRecord.role ?? AUTH_CONSTANTS.ROLE_MEMBER,
        userRecord.user_permissions ?? [],
      ]);
      await client.query(AUTH_QUERIES.FLOW_CREATE_USER.INSERT_USER_ORG, [userRecord.id, userRecord.org_id, userRecord.role ?? AUTH_CONSTANTS.ROLE_MEMBER]);
      await client.query('COMMIT');
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  }

  async listUsersByOrgId(orgId: string): Promise<AuthUserRecord[]> {
    const client = await this.pool.connect();
    try {
      const res = await client.query(AUTH_QUERIES.FLOW_CREATE_USER.LIST_BY_ORG, [orgId]);
      return res.rows.map((row: any) => ({
        id: row.id,
        email: row.email,
        password_hash: row.password_hash,
        name: row.name,
        org_id: row.org_id,
        org_name: row.org_name,
        role: row.role,
        blocked: row.blocked,
        user_permissions: row.user_permissions ?? [],
      }));
    } finally {
      client.release();
    }
  }

  async blockUser(userId: string): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query(AUTH_QUERIES.FLOW_BLOCK_USER.BLOCK_USER, [userId]);
    } finally {
      client.release();
    }
  }

  async unblockUser(userId: string): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query(AUTH_QUERIES.FLOW_CREATE_USER.UNBLOCK_USER, [userId]);
    } finally {
      client.release();
    }
  }

  async deleteUser(userId: string): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query(AUTH_QUERIES.FLOW_DELETE_USER.SOFT_DELETE_USER, [userId]);
    } finally {
      client.release();
    }
  }

  async updateUserProfile(userId: string, patch: { name?: string }): Promise<void> {
    const client = await this.pool.connect();
    try {
      if (patch.name) await client.query(AUTH_QUERIES.FLOW_CREATE_USER.UPDATE_PROFILE_NAME, [patch.name, userId]);
    } finally {
      client.release();
    }
  }

  async updateUserRole(userId: string, role: string): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query(AUTH_QUERIES.FLOW_CREATE_USER.UPDATE_ROLE, [role, userId]);
    } finally {
      client.release();
    }
  }

  async updateUserPermissions(userId: string, permissions: string[]): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query(AUTH_QUERIES.FLOW_CREATE_USER.UPDATE_PERMISSIONS, [permissions, userId]);
    } finally {
      client.release();
    }
  }

  async purgeExpiredSoftDeletes(): Promise<number> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      const r1 = await client.query(AUTH_QUERIES.FLOW_RETENTION_PURGE.PURGE_ORGS);
      const r2 = await client.query(AUTH_QUERIES.FLOW_RETENTION_PURGE.PURGE_USERS);
      const r3 = await client.query(AUTH_QUERIES.FLOW_RETENTION_PURGE.PURGE_KEYS);
      const r4 = await client.query(AUTH_QUERIES.FLOW_RETENTION_PURGE.PURGE_LOGS);
      const r5 = await client.query(AUTH_QUERIES.FLOW_RETENTION_PURGE.PURGE_RESETS);
      const r6 = await client.query(AUTH_QUERIES.FLOW_RETENTION_PURGE.PURGE_DENYLIST, [Date.now()]);
      await client.query('COMMIT');
      return (r1.rowCount ?? 0) + (r2.rowCount ?? 0) + (r3.rowCount ?? 0) + (r4.rowCount ?? 0) + (r5.rowCount ?? 0) + (r6.rowCount ?? 0);
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  }

  async findUserByEmail(email: string): Promise<AuthUserRecord | null> {
    return withSpan('DB SELECT findUserByEmail', async (span) => {
      span.setAttribute('db.system', 'postgresql');
      span.setAttribute('db.operation', 'SELECT');
      span.setAttribute('db.sql.table', 'users');
      const client = await this.pool.connect();
      try {
        const res = await client.query(AUTH_QUERIES.FLOW_SIGN_IN.FIND_USER_BY_EMAIL, [email]);
        if (res.rows.length === 0) return null;
        const row = res.rows[0];
        return {
          id: row.id,
          email: row.email,
          password_hash: row.password_hash,
          name: row.name,
          org_id: row.org_id,
          org_name: row.org_name,
          role: row.role,
          blocked: row.blocked,
          user_permissions: row.user_permissions ?? [],
        };
      } finally {
        client.release();
      }
    }, { kind: SpanKind.CLIENT });
  }

  async findUserById(id: string): Promise<AuthUserRecord | null> {
    const client = await this.pool.connect();
    try {
      const res = await client.query(AUTH_QUERIES.FLOW_SESSION_VERIFY.FIND_USER_BY_ID, [id]);
      if (res.rows.length === 0) return null;
      const row = res.rows[0];
      return {
        id: row.id,
        email: row.email,
        password_hash: row.password_hash,
        name: row.name,
        org_id: row.org_id,
        org_name: row.org_name,
        role: row.role,
        blocked: row.blocked,
        user_permissions: row.user_permissions ?? [],
      };
    } finally {
      client.release();
    }
  }

  async createOrganizationAndUser(userRecord: AuthUserRecord): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      const orgCheck = await client.query(AUTH_QUERIES.FLOW_SIGN_UP.CHECK_ORG_EXISTS, [userRecord.org_name, userRecord.org_name.toLowerCase()]);
      if (orgCheck.rows.length > 0) {
        throw new Error(`Organization name already exists: ${userRecord.org_name}`);
      }

      await client.query(AUTH_QUERIES.FLOW_SIGN_UP.INSERT_ORG, [userRecord.org_id, userRecord.org_name, userRecord.org_name.toLowerCase()]);
      await this.setTenantRlsContext(client, userRecord.org_id);
      await client.query(AUTH_QUERIES.FLOW_SIGN_UP.INSERT_USER, [
        userRecord.id,
        userRecord.email,
        userRecord.password_hash,
        userRecord.name,
        userRecord.org_id,
        userRecord.org_name,
        userRecord.role ?? AUTH_CONSTANTS.ROLE_ADMIN,
        userRecord.user_permissions ?? [],
      ]);
      await client.query(AUTH_QUERIES.FLOW_SIGN_UP.INSERT_USER_ORG, [userRecord.id, userRecord.org_id, userRecord.role ?? AUTH_CONSTANTS.ROLE_ADMIN]);
      await client.query('COMMIT');
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  }

  async recordAuditLog(logRecord: AuditLogRecord): Promise<void> {
    return withSpan('DB INSERT recordAuditLog', async (span) => {
      span.setAttribute('db.system', 'postgresql');
      span.setAttribute('db.operation', 'INSERT');
      span.setAttribute('db.sql.table', 'audit_logs');
      const client = await this.pool.connect();
      try {
        await this.setTenantRlsContext(client, logRecord.org_id);
        await client.query(AUTH_QUERIES.FLOW_SIGN_IN.RECORD_AUDIT_LOG, [
          logRecord.id,
          logRecord.user_id,
          logRecord.org_id,
          logRecord.event_type,
          logRecord.ip_address,
          logRecord.user_agent,
          logRecord.timestamp_ms,
        ]);
      } finally {
        client.release();
      }
    }, { kind: SpanKind.CLIENT });
  }

  async savePasswordResetToken(tokenHash: string, userId: string, expiresAtMs: number): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query(AUTH_QUERIES.FLOW_FORGOT_PASSWORD.INSERT_RESET_TOKEN, [tokenHash, userId, expiresAtMs, false]);
    } finally {
      client.release();
    }
  }

  async findPasswordResetToken(tokenHash: string): Promise<{ tokenHash: string; userId: string; expiresAtMs: number; used: boolean } | null> {
    const client = await this.pool.connect();
    try {
      const res = await client.query(AUTH_QUERIES.FLOW_FORGOT_PASSWORD.FIND_RESET_TOKEN, [tokenHash]);
      if (res.rows.length === 0) return null;
      const row = res.rows[0];
      return {
        tokenHash: row.token_hash,
        userId: row.user_id,
        expiresAtMs: parseInt(row.expires_at_ms, 10),
        used: row.used,
      };
    } finally {
      client.release();
    }
  }

  async updateUserPassword(userId: string, newPasswordHash: string): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query(AUTH_QUERIES.FLOW_RESET_PASSWORD.UPDATE_PASSWORD_HASH, [newPasswordHash, userId]);
    } finally {
      client.release();
    }
  }

  async markPasswordResetTokenUsed(tokenHash: string): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query(AUTH_QUERIES.FLOW_RESET_PASSWORD.MARK_TOKEN_USED, [tokenHash]);
    } finally {
      client.release();
    }
  }

  async saveApiKey(keyRecord: ApiKeyRecord): Promise<void> {
    const client = await this.pool.connect();
    try {
      await this.setTenantRlsContext(client, keyRecord.org_id);
      await client.query(AUTH_QUERIES.FLOW_CREATE_API_KEY.INSERT_API_KEY, [
        keyRecord.key_id,
        keyRecord.org_id,
        keyRecord.key_type,
        keyRecord.key_hash,
        keyRecord.prefix,
        keyRecord.name,
        keyRecord.permissions,
        keyRecord.created_at_ms,
        keyRecord.revoked,
      ]);
    } finally {
      client.release();
    }
  }

  async listApiKeysByOrgId(orgId: string): Promise<ApiKeyRecord[]> {
    const client = await this.pool.connect();
    try {
      const res = await client.query(AUTH_QUERIES.FLOW_CREATE_API_KEY.LIST_BY_ORG, [orgId]);
      return res.rows.map((row: any) => ({
        key_id: row.key_id,
        org_id: row.org_id,
        key_type: row.key_type,
        key_hash: row.key_hash,
        prefix: row.prefix,
        name: row.name,
        permissions: row.permissions,
        created_at_ms: parseInt(row.created_at_ms, 10),
        revoked: row.revoked,
      }));
    } finally {
      client.release();
    }
  }

  async findApiKeyByHash(hash: string): Promise<ApiKeyRecord | null> {
    const client = await this.pool.connect();
    try {
      const res = await client.query(AUTH_QUERIES.FLOW_VERIFY_API_KEY.FIND_API_KEY_BY_HASH, [hash]);
      if (res.rows.length === 0) return null;
      const row = res.rows[0];
      return {
        key_id: row.key_id,
        org_id: row.org_id,
        key_type: row.key_type,
        key_hash: row.key_hash,
        prefix: row.prefix,
        name: row.name,
        permissions: row.permissions,
        created_at_ms: parseInt(row.created_at_ms, 10),
        revoked: row.revoked,
      };
    } finally {
      client.release();
    }
  }

  async revokeApiKey(keyId: string): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query(AUTH_QUERIES.FLOW_REVOKE_API_KEY.REVOKE_API_KEY_BY_ID, [keyId]);
    } finally {
      client.release();
    }
  }

  async fetchUserAuditLogs(userId: string, filters?: { event_type?: string; from_ms?: number; to_ms?: number }): Promise<AuditLogRecord[]> {
    const client = await this.pool.connect();
    try {
      let sql = 'SELECT id, user_id, org_id, event_type, ip_address, user_agent, timestamp_ms FROM auth_audit_logs WHERE user_id = $1 AND deleted_at IS NULL';
      const params: any[] = [userId];
      if (filters?.event_type) { params.push(filters.event_type); sql += ` AND event_type = $${params.length}`; }
      if (filters?.from_ms) { params.push(filters.from_ms); sql += ` AND timestamp_ms >= $${params.length}`; }
      if (filters?.to_ms) { params.push(filters.to_ms); sql += ` AND timestamp_ms <= $${params.length}`; }
      sql += ' ORDER BY timestamp_ms DESC LIMIT 100';
      const res = await client.query(sql, params);
      return res.rows.map((row: any) => ({
        id: row.id,
        user_id: row.user_id,
        org_id: row.org_id,
        event_type: row.event_type,
        ip_address: row.ip_address,
        user_agent: row.user_agent,
        timestamp_ms: parseInt(row.timestamp_ms, 10),
      }));
    } finally {
      client.release();
    }
  }

  async addTokenToDenylist(token: string, expiresAtMs: number): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query(AUTH_QUERIES.FLOW_SESSION_VERIFY.ADD_TOKEN_DENYLIST, [token, expiresAtMs]);
    } finally {
      client.release();
    }
  }

  async isTokenDenylisted(token: string): Promise<boolean> {
    const client = await this.pool.connect();
    try {
      const res = await client.query(AUTH_QUERIES.FLOW_SESSION_VERIFY.CHECK_TOKEN_DENYLIST, [token, Date.now()]);
      return res.rows.length > 0;
    } finally {
      client.release();
    }
  }
}
