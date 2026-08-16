import type { AuthRepositoryPort } from './repository';
import type { SignInCredentials, CreateApiKeyInput } from './types';
import type { ApiKeyRecord, AuthTokenPayload } from '../../shared/types/auth.types';
import { InvalidCredentialsError, ApiKeyRevokedError } from '../../shared/errors/auth.errors';
import { verifyPassword, hashApiKey } from '../../shared/utils/argon2.util';
import { createToken, verifyToken } from '../../shared/utils/jwt.util';
import { AUTH_CONSTANTS } from '../../shared/constants/auth.constants';

export class AuthService {
  constructor(private readonly repo: AuthRepositoryPort) {}

  async signIn(credentials: SignInCredentials): Promise<{ token: string; payload: AuthTokenPayload }> {
    const user = await this.repo.findUserByEmail(credentials.email);
    if (!user) {
      throw new InvalidCredentialsError();
    }

    const isValid = await verifyPassword(credentials.password, user.password_hash);
    if (!isValid) {
      throw new InvalidCredentialsError();
    }

    const token = createToken(user.id, user.email, {
      org_id: user.org_id,
      org_name: user.org_name,
      role: user.role,
    });

    const payload = verifyToken(token);
    return { token, payload };
  }

  async validateSession(token: string): Promise<AuthTokenPayload> {
    return verifyToken(token);
  }

  async generateApiKey(input: CreateApiKeyInput): Promise<{ rawKey: string; keyRecord: ApiKeyRecord }> {
    const keyId = `${AUTH_CONSTANTS.API_KEY_PREFIX}${Math.random().toString(36).substring(2, 9)}`;
    const secret = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    const rawKey = `${AUTH_CONSTANTS.API_KEY_PREFIX}${input.org_id}_${secret}`;
    const keyHash = await hashApiKey(rawKey);

    const keyRecord: ApiKeyRecord = {
      key_id: keyId,
      org_id: input.org_id,
      key_hash: keyHash,
      prefix: `${AUTH_CONSTANTS.API_KEY_PREFIX}${input.org_id}`,
      name: input.name,
      created_at_ms: Date.now(),
      revoked: false,
    };

    await this.repo.saveApiKey(keyRecord);
    return { rawKey, keyRecord };
  }

  async verifyApiKey(rawKey: string): Promise<ApiKeyRecord> {
    const keyHash = await hashApiKey(rawKey);
    const record = await this.repo.findApiKeyByHash(keyHash);
    if (!record || record.revoked) {
      throw new ApiKeyRevokedError();
    }
    return record;
  }
}
