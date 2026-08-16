import type { AuthRepositoryPort } from '../../../features/auth/repository';
import type { AuthUserRecord, AuditLogRecord } from '../../../features/auth/types';
import type { ApiKeyRecord } from '../../../shared/types/auth.types';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';
import { AUTH_QUERIES } from '../../../features/auth/queries/auth.queries';

export class AlloyDBOmniAuthAdapter implements AuthRepositoryPort {
  private readonly mockUsers = new Map<string, AuthUserRecord>();
  private readonly mockApiKeys = new Map<string, ApiKeyRecord>();
  private readonly mockAuditLogs = new Map<string, AuditLogRecord>();
  private readonly mockResets = new Map<string, { tokenHash: string; userId: string; expiresAtMs: number; used: boolean }>();
  public readonly queries = AUTH_QUERIES;

  constructor() {
    this.mockUsers.set(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL, {
      id: AUTH_CONSTANTS.DEFAULT_ADMIN_ID,
      email: AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL,
      password_hash: AUTH_CONSTANTS.DEFAULT_ADMIN_PASSWORD_HASH,
      name: AUTH_CONSTANTS.DEFAULT_ADMIN_NAME,
      org_id: AUTH_CONSTANTS.DEFAULT_ORG_ID,
      org_name: AUTH_CONSTANTS.DEFAULT_ORG_NAME,
      role: AUTH_CONSTANTS.ROLE_ADMIN,
    });
  }

  public getFlowQuery(flow: keyof typeof AUTH_QUERIES): string {
    return JSON.stringify(this.queries[flow]);
  }

  async findUserByEmail(email: string): Promise<AuthUserRecord | null> {
    this.getFlowQuery('FLOW_SIGN_IN');
    return this.mockUsers.get(email) ?? null;
  }

  async findUserById(id: string): Promise<AuthUserRecord | null> {
    this.getFlowQuery('FLOW_SESSION_VERIFY');
    return [...this.mockUsers.values()].find((u) => u.id === id) ?? null;
  }

  async createOrganizationAndUser(userRecord: AuthUserRecord): Promise<void> {
    this.getFlowQuery('FLOW_SIGN_UP');
    const existingOrg = [...this.mockUsers.values()].find((u) => u.org_name.toLowerCase() === userRecord.org_name.toLowerCase());
    if (existingOrg) {
      throw new Error(`Organization name already exists: ${userRecord.org_name}`);
    }
    this.mockUsers.set(userRecord.email, userRecord);
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
    return this.mockResets.get(tokenHash) ?? null;
  }

  async updateUserPassword(userId: string, newPasswordHash: string): Promise<void> {
    this.getFlowQuery('FLOW_RESET_PASSWORD');
    for (const user of this.mockUsers.values()) {
      if (user.id === userId) {
        user.password_hash = newPasswordHash;
      }
    }
  }

  async markPasswordResetTokenUsed(tokenHash: string): Promise<void> {
    this.getFlowQuery('FLOW_RESET_PASSWORD');
    const reset = this.mockResets.get(tokenHash);
    if (reset) {
      reset.used = true;
    }
  }

  async saveApiKey(keyRecord: ApiKeyRecord): Promise<void> {
    this.getFlowQuery('FLOW_CREATE_API_KEY');
    this.mockApiKeys.set(keyRecord.key_hash, keyRecord);
  }

  async findApiKeyByHash(hash: string): Promise<ApiKeyRecord | null> {
    this.getFlowQuery('FLOW_VERIFY_API_KEY');
    return this.mockApiKeys.get(hash) ?? null;
  }

  async revokeApiKey(keyId: string): Promise<void> {
    this.getFlowQuery('FLOW_REVOKE_API_KEY');
    for (const record of this.mockApiKeys.values()) {
      if (record.key_id === keyId) {
        record.revoked = true;
      }
    }
  }
}
