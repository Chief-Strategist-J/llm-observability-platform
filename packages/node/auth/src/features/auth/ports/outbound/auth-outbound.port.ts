import type { AuthUserRecord, AuditLogRecord } from '../../types';
import type { ApiKeyRecord } from '../../../../shared/types/auth.types';
import type { OrganizationRecord } from '../../repository';

export interface IAuthOutboundPort {
  listOrganizationsByUserId(userId: string): Promise<OrganizationRecord[]>;
  getOrganizationById(orgId: string): Promise<OrganizationRecord | null>;
  createOrganization(org: OrganizationRecord, creatorUserId?: string): Promise<void>;
  updateOrganization(orgId: string, patch: { name?: string; slug?: string }): Promise<void>;
  deleteOrganization(orgId: string): Promise<void>;
  listUsersByOrgId(orgId: string): Promise<AuthUserRecord[]>;
  createUser(userRecord: AuthUserRecord): Promise<void>;
  blockUser(userId: string): Promise<void>;
  unblockUser(userId: string): Promise<void>;
  deleteUser(userId: string): Promise<void>;
  updateUserProfile(userId: string, patch: { name?: string }): Promise<void>;
  updateUserRole(userId: string, role: string): Promise<void>;
  updateUserPermissions(userId: string, permissions: string[]): Promise<void>;
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
  listApiKeysByOrgId(orgId: string): Promise<ApiKeyRecord[]>;
  findApiKeyByHash(hash: string): Promise<ApiKeyRecord | null>;
  revokeApiKey(keyId: string): Promise<void>;
  fetchUserAuditLogs(userId: string, filters?: { event_type?: string; from_ms?: number; to_ms?: number }): Promise<AuditLogRecord[]>;
  addTokenToDenylist(token: string, expiresAtMs: number): Promise<void>;
  isTokenDenylisted(token: string): Promise<boolean>;
}
