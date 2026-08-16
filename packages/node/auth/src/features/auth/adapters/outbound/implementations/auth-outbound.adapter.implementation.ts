import type { IAuthOutboundAdapter } from '../auth-outbound.adapter';
import type { AuthRepositoryPort } from '../../../repository';
import type { AuthUserRecord, AuditLogRecord } from '../../../types';
import type { ApiKeyRecord } from '../../../../../shared/types/auth.types';

export class AuthOutboundAdapterImplementation implements IAuthOutboundAdapter {
  constructor(private readonly repository: AuthRepositoryPort) {}

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

  findPasswordResetToken(
    tokenHash: string
  ): Promise<{ tokenHash: string; userId: string; expiresAtMs: number; used: boolean } | null> {
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

  findApiKeyByHash(hash: string): Promise<ApiKeyRecord | null> {
    return this.repository.findApiKeyByHash(hash);
  }

  revokeApiKey(keyId: string): Promise<void> {
    return this.repository.revokeApiKey(keyId);
  }
}
