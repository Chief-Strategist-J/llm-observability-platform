import type { AuthUserRecord } from './types';
import type { ApiKeyRecord } from '../../shared/types/auth.types';

export interface AuthRepositoryPort {
  findUserByEmail(email: string): Promise<AuthUserRecord | null>;
  findUserById(id: string): Promise<AuthUserRecord | null>;
  saveApiKey(keyRecord: ApiKeyRecord): Promise<void>;
  findApiKeyByHash(hash: string): Promise<ApiKeyRecord | null>;
  revokeApiKey(keyId: string): Promise<void>;
}
