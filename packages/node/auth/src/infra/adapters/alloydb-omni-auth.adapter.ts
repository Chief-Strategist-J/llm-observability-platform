import type { AuthRepositoryPort } from '../../features/auth/repository';
import type { AuthUserRecord } from '../../features/auth/types';
import type { ApiKeyRecord } from '../../shared/types/auth.types';
import { AUTH_CONSTANTS } from '../../shared/constants/auth.constants';

export class AlloyDBOmniAuthAdapter implements AuthRepositoryPort {
  private readonly mockUsers = new Map<string, AuthUserRecord>();
  private readonly mockApiKeys = new Map<string, ApiKeyRecord>();

  constructor() {
    this.mockUsers.set(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL, {
      id: AUTH_CONSTANTS.DEFAULT_ADMIN_ID,
      email: AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL,
      password_hash: AUTH_CONSTANTS.DEFAULT_ADMIN_PASSWORD_HASH,
      name: AUTH_CONSTANTS.DEFAULT_ADMIN_NAME,
      org_id: AUTH_CONSTANTS.DEFAULT_ORG_ID,
      org_name: AUTH_CONSTANTS.DEFAULT_ORG_NAME,
      role: AUTH_CONSTANTS.DEFAULT_ADMIN_ROLE,
    });
  }

  async findUserByEmail(email: string): Promise<AuthUserRecord | null> {
    return this.mockUsers.get(email) ?? null;
  }

  async findUserById(id: string): Promise<AuthUserRecord | null> {
    return [...this.mockUsers.values()].find((u) => u.id === id) ?? null;
  }

  async saveApiKey(keyRecord: ApiKeyRecord): Promise<void> {
    this.mockApiKeys.set(keyRecord.key_hash, keyRecord);
  }

  async findApiKeyByHash(hash: string): Promise<ApiKeyRecord | null> {
    return this.mockApiKeys.get(hash) ?? null;
  }

  async revokeApiKey(keyId: string): Promise<void> {
    for (const record of this.mockApiKeys.values()) {
      if (record.key_id === keyId) {
        record.revoked = true;
      }
    }
  }
}
