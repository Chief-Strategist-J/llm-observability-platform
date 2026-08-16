import type { AuthRepositoryPort } from '../../../features/auth/repository';
import type { AuthUserRecord, AuditLogRecord } from '../../../features/auth/types';
import type { ApiKeyRecord } from '../../../shared/types/auth.types';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';
import { AUTH_QUERIES } from '../../../features/auth/queries/auth.queries';

export class AlloyDBOmniAuthAdapter implements AuthRepositoryPort {
  private readonly mockOrgs = new Map<string, { id: string; name: string; slug: string; deleted_at?: number }>();
  private readonly mockUsers = new Map<string, AuthUserRecord & { deleted_at?: number }>();
  private readonly mockApiKeys = new Map<string, ApiKeyRecord & { deleted_at?: number }>();
  private readonly mockAuditLogs = new Map<string, AuditLogRecord & { deleted_at?: number }>();
  private readonly mockResets = new Map<string, { tokenHash: string; userId: string; expiresAtMs: number; used: boolean; deleted_at?: number }>();
  public readonly queries = AUTH_QUERIES;

  constructor() {
    this.mockOrgs.set(AUTH_CONSTANTS.DEFAULT_ORG_ID, {
      id: AUTH_CONSTANTS.DEFAULT_ORG_ID,
      name: AUTH_CONSTANTS.DEFAULT_ORG_NAME,
      slug: 'acme-observability',
    });

    this.mockUsers.set(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL, {
      id: AUTH_CONSTANTS.DEFAULT_ADMIN_ID,
      email: AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL,
      password_hash: AUTH_CONSTANTS.DEFAULT_ADMIN_PASSWORD_HASH,
      name: AUTH_CONSTANTS.DEFAULT_ADMIN_NAME,
      org_id: AUTH_CONSTANTS.DEFAULT_ORG_ID,
      org_name: AUTH_CONSTANTS.DEFAULT_ORG_NAME,
      role: AUTH_CONSTANTS.ROLE_ADMIN,
      blocked: false,
      user_permissions: [AUTH_CONSTANTS.PERMISSION_ADMIN_ALL],
    });
  }

  public getFlowQuery(flow: keyof typeof AUTH_QUERIES): string {
    return JSON.stringify(this.queries[flow]);
  }

  async createOrganization(org: { id: string; name: string; slug: string }): Promise<void> {
    this.getFlowQuery('FLOW_CREATE_ORGANIZATION');
    const existing = [...this.mockOrgs.values()].find((o) => !o.deleted_at && o.name.toLowerCase() === org.name.toLowerCase());
    if (existing) {
      throw new Error(`Organization name already exists: ${org.name}`);
    }
    this.mockOrgs.set(org.id, { ...org });
  }

  async deleteOrganization(orgId: string): Promise<void> {
    this.getFlowQuery('FLOW_DELETE_ORGANIZATION');
    const now = Date.now();
    const org = this.mockOrgs.get(orgId);
    if (org) org.deleted_at = now;

    for (const user of this.mockUsers.values()) {
      if (user.org_id === orgId) user.deleted_at = now;
    }
    for (const key of this.mockApiKeys.values()) {
      if (key.org_id === orgId) key.deleted_at = now;
    }
    for (const log of this.mockAuditLogs.values()) {
      if (log.org_id === orgId) log.deleted_at = now;
    }
  }

  async createUser(userRecord: AuthUserRecord): Promise<void> {
    this.getFlowQuery('FLOW_CREATE_USER');
    const existing = [...this.mockUsers.values()].find((u) => !u.deleted_at && u.email === userRecord.email);
    if (existing) {
      throw new Error(`User with email ${userRecord.email} already exists`);
    }
    this.mockUsers.set(userRecord.email, { ...userRecord });
  }

  async blockUser(userId: string): Promise<void> {
    this.getFlowQuery('FLOW_BLOCK_USER');
    for (const user of this.mockUsers.values()) {
      if (user.id === userId && !user.deleted_at) {
        user.blocked = true;
      }
    }
  }

  async deleteUser(userId: string): Promise<void> {
    this.getFlowQuery('FLOW_DELETE_USER');
    const now = Date.now();
    for (const user of this.mockUsers.values()) {
      if (user.id === userId) {
        user.deleted_at = now;
      }
    }
  }

  async purgeExpiredSoftDeletes(): Promise<number> {
    this.getFlowQuery('FLOW_RETENTION_PURGE');
    const cutoff = Date.now() - 30 * 24 * 60 * 60 * 1000;
    let purged = 0;

    for (const [id, org] of this.mockOrgs.entries()) {
      if (org.deleted_at && org.deleted_at < cutoff) {
        this.mockOrgs.delete(id);
        purged++;
      }
    }
    for (const [email, user] of this.mockUsers.entries()) {
      if (user.deleted_at && user.deleted_at < cutoff) {
        this.mockUsers.delete(email);
        purged++;
      }
    }
    for (const [key, keyRecord] of this.mockApiKeys.entries()) {
      if (keyRecord.deleted_at && keyRecord.deleted_at < cutoff) {
        this.mockApiKeys.delete(key);
        purged++;
      }
    }
    return purged;
  }

  async findUserByEmail(email: string): Promise<AuthUserRecord | null> {
    this.getFlowQuery('FLOW_SIGN_IN');
    const user = this.mockUsers.get(email);
    if (!user || user.deleted_at) return null;
    return user;
  }

  async findUserById(id: string): Promise<AuthUserRecord | null> {
    this.getFlowQuery('FLOW_SESSION_VERIFY');
    const user = [...this.mockUsers.values()].find((u) => u.id === id && !u.deleted_at);
    return user ?? null;
  }

  async createOrganizationAndUser(userRecord: AuthUserRecord): Promise<void> {
    this.getFlowQuery('FLOW_SIGN_UP');
    const existingOrg = [...this.mockOrgs.values()].find((o) => !o.deleted_at && o.name.toLowerCase() === userRecord.org_name.toLowerCase());
    if (existingOrg) {
      throw new Error(`Organization name already exists: ${userRecord.org_name}`);
    }
    this.mockOrgs.set(userRecord.org_id, {
      id: userRecord.org_id,
      name: userRecord.org_name,
      slug: userRecord.org_name.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
    });
    this.mockUsers.set(userRecord.email, { ...userRecord });
  }

  async recordAuditLog(logRecord: AuditLogRecord): Promise<void> {
    this.getFlowQuery('FLOW_SIGN_IN');
    this.mockAuditLogs.set(logRecord.id, logRecord);
  }

  async savePasswordResetToken(tokenHash: string, userId: string, expiresAtMs: number): Promise<void> {
    this.getFlowQuery('FLOW_FORGOT_PASSWORD');
    this.mockResets.set(tokenHash, { tokenHash, userId, expiresAtMs, used: false });
  }

  async findPasswordResetToken(tokenHash: string): Promise<{ tokenHash: string; userId: string; expiresAtMs: number; used: boolean } | null> {
    this.getFlowQuery('FLOW_FORGOT_PASSWORD');
    const reset = this.mockResets.get(tokenHash);
    if (!reset || reset.deleted_at) return null;
    return reset;
  }

  async updateUserPassword(userId: string, newPasswordHash: string): Promise<void> {
    this.getFlowQuery('FLOW_RESET_PASSWORD');
    for (const user of this.mockUsers.values()) {
      if (user.id === userId && !user.deleted_at) {
        user.password_hash = newPasswordHash;
      }
    }
  }

  async markPasswordResetTokenUsed(tokenHash: string): Promise<void> {
    this.getFlowQuery('FLOW_RESET_PASSWORD');
    const reset = this.mockResets.get(tokenHash);
    if (reset && !reset.deleted_at) {
      reset.used = true;
    }
  }

  async saveApiKey(keyRecord: ApiKeyRecord): Promise<void> {
    this.getFlowQuery('FLOW_CREATE_API_KEY');
    this.mockApiKeys.set(keyRecord.key_hash, keyRecord);
  }

  async findApiKeyByHash(hash: string): Promise<ApiKeyRecord | null> {
    this.getFlowQuery('FLOW_VERIFY_API_KEY');
    const key = this.mockApiKeys.get(hash);
    if (!key || key.deleted_at) return null;
    return key;
  }

  async revokeApiKey(keyId: string): Promise<void> {
    this.getFlowQuery('FLOW_REVOKE_API_KEY');
    for (const record of this.mockApiKeys.values()) {
      if (record.key_id === keyId && !record.deleted_at) {
        record.revoked = true;
      }
    }
  }

  async fetchUserAuditLogs(userId: string): Promise<AuditLogRecord[]> {
    this.getFlowQuery('FLOW_AUDIT_LOGS');
    return [...this.mockAuditLogs.values()].filter((log) => log.user_id === userId && !log.deleted_at);
  }
}
