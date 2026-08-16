import type { AuthUserRecord, AuditLogRecord } from './types';
import type { ApiKeyRecord } from '../../shared/types/auth.types';

export interface AuthRepositoryPort {
  createOrganization(org: { id: string; name: string; slug: string }): Promise<void>;
  deleteOrganization(orgId: string): Promise<void>;
  createUser(userRecord: AuthUserRecord): Promise<void>;
  blockUser(userId: string): Promise<void>;
  deleteUser(userId: string): Promise<void>;
  purgeExpiredSoftDeletes(): Promise<number>;
  findUserByEmail(email: string): Promise<AuthUserRecord | null>;
  findUserById(id: string): Promise<AuthUserRecord | null>;
  createOrganizationAndUser(userRecord: AuthUserRecord): Promise<void>;
  recordAuditLog(logRecord: AuditLogRecord): Promise<void>;
  savePasswordResetToken(tokenHash: string, userId: string, expiresAtMs: number): Promise<void>;
  findPasswordResetToken(tokenHash: string): Promise<{ tokenHash: string; userId: string; expiresAtMs: number; used: boolean } | null>;
  updateUserPassword(userId: string, newPasswordHash: string): Promise<void>;
  markPasswordResetTokenUsed(tokenHash: string): Promise<void>;
  saveApiKey(keyRecord: ApiKeyRecord): Promise<void>;
  findApiKeyByHash(hash: string): Promise<ApiKeyRecord | null>;
  revokeApiKey(keyId: string): Promise<void>;
  fetchUserAuditLogs(userId: string): Promise<AuditLogRecord[]>;
}
