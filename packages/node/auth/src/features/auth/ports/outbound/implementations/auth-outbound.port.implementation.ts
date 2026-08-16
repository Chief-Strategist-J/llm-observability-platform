import type { IAuthOutboundPort } from '../auth-outbound.port';
import type { AuthRepositoryPort, OrganizationRecord } from '../../../repository';
import type { AuthUserRecord, AuditLogRecord } from '../../../types';
import type { ApiKeyRecord } from '../../../../../shared/types/auth.types';

export class AuthOutboundPortImplementation implements IAuthOutboundPort {
  constructor(private readonly repository: AuthRepositoryPort) {}

  listOrganizationsByUserId(userId: string): Promise<OrganizationRecord[]> {
    return this.repository.listOrganizationsByUserId(userId);
  }

  getOrganizationById(orgId: string): Promise<OrganizationRecord | null> {
    return this.repository.getOrganizationById(orgId);
  }

  createOrganization(org: OrganizationRecord, creatorUserId?: string): Promise<void> {
    return this.repository.createOrganization(org, creatorUserId);
  }

  updateOrganization(orgId: string, patch: { name?: string; slug?: string }): Promise<void> {
    return this.repository.updateOrganization(orgId, patch);
  }

  deleteOrganization(orgId: string): Promise<void> {
    return this.repository.deleteOrganization(orgId);
  }

  listUsersByOrgId(orgId: string): Promise<AuthUserRecord[]> {
    return this.repository.listUsersByOrgId(orgId);
  }

  createUser(userRecord: AuthUserRecord): Promise<void> {
    return this.repository.createUser(userRecord);
  }

  blockUser(userId: string): Promise<void> {
    return this.repository.blockUser(userId);
  }

  unblockUser(userId: string): Promise<void> {
    return this.repository.unblockUser(userId);
  }

  deleteUser(userId: string): Promise<void> {
    return this.repository.deleteUser(userId);
  }

  updateUserProfile(userId: string, patch: { name?: string }): Promise<void> {
    return this.repository.updateUserProfile(userId, patch);
  }

  updateUserRole(userId: string, role: string): Promise<void> {
    return this.repository.updateUserRole(userId, role);
  }

  updateUserPermissions(userId: string, permissions: string[]): Promise<void> {
    return this.repository.updateUserPermissions(userId, permissions);
  }

  purgeExpiredSoftDeletes(): Promise<number> {
    return this.repository.purgeExpiredSoftDeletes();
  }

  findUserByEmail(email: string): Promise<AuthUserRecord | null> {
    return this.repository.findUserByEmail(email);
  }

  findUserById(id: string): Promise<AuthUserRecord | null> {
    return this.repository.findUserById(id);
  }

  createOrganizationAndUser(userRecord: AuthUserRecord): Promise<void> {
    return this.repository.createOrganizationAndUser(userRecord);
  }

  recordAuditLog(logRecord: AuditLogRecord): Promise<void> {
    return this.repository.recordAuditLog(logRecord);
  }

  savePasswordResetToken(tokenHash: string, userId: string, expiresAtMs: number): Promise<void> {
    return this.repository.savePasswordResetToken(tokenHash, userId, expiresAtMs);
  }

  findPasswordResetToken(tokenHash: string): Promise<{ tokenHash: string; userId: string; expiresAtMs: number; used: boolean } | null> {
    return this.repository.findPasswordResetToken(tokenHash);
  }

  updateUserPassword(userId: string, newPasswordHash: string): Promise<void> {
    return this.repository.updateUserPassword(userId, newPasswordHash);
  }

  markPasswordResetTokenUsed(tokenHash: string): Promise<void> {
    return this.repository.markPasswordResetTokenUsed(tokenHash);
  }

  saveApiKey(keyRecord: ApiKeyRecord): Promise<void> {
    return this.repository.saveApiKey(keyRecord);
  }

  listApiKeysByOrgId(orgId: string): Promise<ApiKeyRecord[]> {
    return this.repository.listApiKeysByOrgId(orgId);
  }

  findApiKeyByHash(hash: string): Promise<ApiKeyRecord | null> {
    return this.repository.findApiKeyByHash(hash);
  }

  revokeApiKey(keyId: string): Promise<void> {
    return this.repository.revokeApiKey(keyId);
  }

  fetchUserAuditLogs(userId: string, filters?: { event_type?: string; from_ms?: number; to_ms?: number }): Promise<AuditLogRecord[]> {
    return this.repository.fetchUserAuditLogs(userId, filters);
  }

  addTokenToDenylist(token: string, expiresAtMs: number): Promise<void> {
    return this.repository.addTokenToDenylist(token, expiresAtMs);
  }

  isTokenDenylisted(token: string): Promise<boolean> {
    return this.repository.isTokenDenylisted(token);
  }
}
