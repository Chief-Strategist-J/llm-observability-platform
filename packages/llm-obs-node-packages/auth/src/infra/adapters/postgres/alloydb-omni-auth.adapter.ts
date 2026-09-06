import type { AuthRepositoryPort, OrganizationRecord } from '../../../features/auth/repository';
import type { AuthUserRecord, AuditLogRecord } from '../../../features/auth/types';
import type { ApiKeyRecord } from '../../../shared/types/auth.types';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';
import { AUTH_QUERIES } from '../../../features/auth/queries/auth.queries';

export class AlloyDBOmniAuthAdapter implements AuthRepositoryPort {
  private readonly mockOrgs = new Map<string, OrganizationRecord>();
  private readonly mockUsers = new Map<string, AuthUserRecord & { deleted_at?: number }>();
  private readonly mockUserOrgs = new Map<string, Set<string>>();
  private readonly mockApiKeys = new Map<string, ApiKeyRecord & { deleted_at?: number }>();
  private readonly mockAuditLogs = new Map<string, AuditLogRecord & { deleted_at?: number }>();
  private readonly mockResets = new Map<string, { tokenHash: string; userId: string; expiresAtMs: number; used: boolean; deleted_at?: number }>();
  private readonly tokenDenylist = new Map<string, number>();
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

    this.mockUserOrgs.set(AUTH_CONSTANTS.DEFAULT_ADMIN_ID, new Set([AUTH_CONSTANTS.DEFAULT_ORG_ID]));
  }

  public getFlowQuery(flow: keyof typeof AUTH_QUERIES): string {
    return JSON.stringify(this.queries[flow]);
  }

  async createOrganization(org: OrganizationRecord, creatorUserId?: string): Promise<void> {
    this.getFlowQuery('FLOW_CREATE_ORGANIZATION');
    const existing = [...this.mockOrgs.values()].find((o) => !o.deleted_at && o.name.toLowerCase() === org.name.toLowerCase());
    if (existing) {
      throw new Error(`Organization name already exists: ${org.name}`);
    }
    this.mockOrgs.set(org.id, { ...org });
    if (creatorUserId) {
      if (!this.mockUserOrgs.has(creatorUserId)) this.mockUserOrgs.set(creatorUserId, new Set());
      this.mockUserOrgs.get(creatorUserId)!.add(org.id);
    }
  }

  async listOrganizationsByUserId(userId: string): Promise<OrganizationRecord[]> {
    this.getFlowQuery('FLOW_CREATE_ORGANIZATION');
    const orgIds = this.mockUserOrgs.get(userId) ?? new Set();
    const user = [...this.mockUsers.values()].find((u) => u.id === userId && !u.deleted_at);
    if (user) orgIds.add(user.org_id);

    const result: OrganizationRecord[] = [];
    for (const orgId of orgIds) {
      const org = this.mockOrgs.get(orgId);
      if (org && !org.deleted_at) result.push(org);
    }
    return result;
  }

  async getOrganizationById(orgId: string): Promise<OrganizationRecord | null> {
    this.getFlowQuery('FLOW_CREATE_ORGANIZATION');
    const org = this.mockOrgs.get(orgId);
    if (!org || org.deleted_at) return null;
    return org;
  }

  async updateOrganization(orgId: string, patch: { name?: string; slug?: string }): Promise<void> {
    this.getFlowQuery('FLOW_CREATE_ORGANIZATION');
    const org = this.mockOrgs.get(orgId);
    if (org && !org.deleted_at) {
      if (patch.name) org.name = patch.name;
      if (patch.slug) org.slug = patch.slug;
    }
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
    if (!this.mockUserOrgs.has(userRecord.id)) this.mockUserOrgs.set(userRecord.id, new Set());
    this.mockUserOrgs.get(userRecord.id)!.add(userRecord.org_id);
  }

  async listUsersByOrgId(orgId: string): Promise<AuthUserRecord[]> {
    this.getFlowQuery('FLOW_CREATE_USER');
    return [...this.mockUsers.values()].filter((u) => u.org_id === orgId && !u.deleted_at);
  }

  async blockUser(userId: string): Promise<void> {
    this.getFlowQuery('FLOW_BLOCK_USER');
    for (const user of this.mockUsers.values()) {
      if (user.id === userId && !user.deleted_at) {
        user.blocked = true;
      }
    }
  }

  async unblockUser(userId: string): Promise<void> {
    this.getFlowQuery('FLOW_BLOCK_USER');
    for (const user of this.mockUsers.values()) {
      if (user.id === userId && !user.deleted_at) {
        user.blocked = false;
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

  async updateUserProfile(userId: string, patch: { name?: string }): Promise<void> {
    for (const user of this.mockUsers.values()) {
      if (user.id === userId && !user.deleted_at) {
        if (patch.name) user.name = patch.name;
      }
    }
  }

  async updateUserRole(userId: string, role: string): Promise<void> {
    for (const user of this.mockUsers.values()) {
      if (user.id === userId && !user.deleted_at) {
        (user as any).role = role;
      }
    }
  }

  async updateUserPermissions(userId: string, permissions: string[]): Promise<void> {
    for (const user of this.mockUsers.values()) {
      if (user.id === userId && !user.deleted_at) {
        user.user_permissions = permissions;
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
    for (const [token, expiresAtMs] of this.tokenDenylist.entries()) {
      if (expiresAtMs < Date.now()) {
        this.tokenDenylist.delete(token);
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
    if (!this.mockUserOrgs.has(userRecord.id)) this.mockUserOrgs.set(userRecord.id, new Set());
    this.mockUserOrgs.get(userRecord.id)!.add(userRecord.org_id);
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

  async listApiKeysByOrgId(orgId: string): Promise<ApiKeyRecord[]> {
    this.getFlowQuery('FLOW_VERIFY_API_KEY');
    return [...this.mockApiKeys.values()].filter((k) => k.org_id === orgId && !k.deleted_at);
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

  async fetchUserAuditLogs(userId: string, filters?: { event_type?: string; from_ms?: number; to_ms?: number }): Promise<AuditLogRecord[]> {
    this.getFlowQuery('FLOW_AUDIT_LOGS');
    return [...this.mockAuditLogs.values()].filter((log) => {
      if (log.user_id !== userId || log.deleted_at) return false;
      if (filters?.event_type && log.event_type !== filters.event_type) return false;
      if (filters?.from_ms && log.timestamp_ms < filters.from_ms) return false;
      if (filters?.to_ms && log.timestamp_ms > filters.to_ms) return false;
      return true;
    });
  }

  async addTokenToDenylist(token: string, expiresAtMs: number): Promise<void> {
    this.tokenDenylist.set(token, expiresAtMs);
  }

  async isTokenDenylisted(token: string): Promise<boolean> {
    const exp = this.tokenDenylist.get(token);
    if (!exp) return false;
    if (exp < Date.now()) {
      this.tokenDenylist.delete(token);
      return false;
    }
    return true;
  }
}
