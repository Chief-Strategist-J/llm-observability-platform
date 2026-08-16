import type { AuthRepositoryPort } from '../../features/auth/repository';
import type { AuthUserRecord } from '../../features/auth/types';
import type { ApiKeyRecord } from '../../shared/types/auth.types';

export class PostgresAuthAdapter implements AuthRepositoryPort {
  private readonly mockUsers = new Map<string, AuthUserRecord>();
  private readonly mockApiKeys = new Map<string, ApiKeyRecord>();

  constructor() {
    this.mockUsers.set('admin@observability.io', {
      id: 'usr-admin-001',
      email: 'admin@observability.io',
      password_hash: 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f',
      name: 'Observability Admin',
      org_id: 'org-default-001',
      org_name: 'Acme Observability',
      role: 'admin',
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
