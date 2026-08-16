import { AuthService } from '../../service';
import type { AuthRepositoryPort } from '../../repository';
import type { AuthUserRecord } from '../../types';
import type { ApiKeyRecord } from '../../../../shared/types/auth.types';
import { hashPassword } from '../../../../shared/utils/argon2.util';
import { InvalidCredentialsError } from '../../../../shared/errors/auth.errors';

class MockAuthRepository implements AuthRepositoryPort {
  private users = new Map<string, AuthUserRecord>();
  private apiKeys = new Map<string, ApiKeyRecord>();

  addUser(user: AuthUserRecord): void {
    this.users.set(user.email, user);
  }

  async findUserByEmail(email: string): Promise<AuthUserRecord | null> {
    return this.users.get(email) ?? null;
  }

  async findUserById(id: string): Promise<AuthUserRecord | null> {
    return [...this.users.values()].find((u) => u.id === id) ?? null;
  }

  async saveApiKey(keyRecord: ApiKeyRecord): Promise<void> {
    this.apiKeys.set(keyRecord.key_hash, keyRecord);
  }

  async findApiKeyByHash(hash: string): Promise<ApiKeyRecord | null> {
    return this.apiKeys.get(hash) ?? null;
  }

  async revokeApiKey(keyId: string): Promise<void> {
    for (const record of this.apiKeys.values()) {
      if (record.key_id === keyId) {
        record.revoked = true;
      }
    }
  }
}

export async function runAuthServiceUnitTest(): Promise<boolean> {
  const repo = new MockAuthRepository();
  const pwdHash = await hashPassword('secret123');
  repo.addUser({
    id: 'usr-001',
    email: 'admin@acme.com',
    password_hash: pwdHash,
    name: 'Admin User',
    org_id: 'org-001',
    org_name: 'Acme Corp',
    role: 'admin',
  });

  const service = new AuthService(repo);

  const result = await service.signIn({ email: 'admin@acme.com', password: 'secret123' });
  if (!result.token || result.payload.sub !== 'usr-001') {
    throw new Error('signIn failed');
  }

  try {
    await service.signIn({ email: 'admin@acme.com', password: 'wrongpassword' });
    throw new Error('Expected InvalidCredentialsError');
  } catch (err) {
    if (!(err instanceof InvalidCredentialsError)) throw err;
  }

  return true;
}
