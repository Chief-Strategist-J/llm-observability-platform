import type { AuthRepositoryPort } from '../repository';
import type { CreateApiKeyInput, VerifyApiKeyInput } from '../types';
import type { ApiKeyRecord } from '../../../shared/types/auth.types';
import { CreateApiKeyInputSchema, VerifyApiKeyInputSchema } from '../schema/auth.schema';
import { ApiKeyRevokedError, InsufficientPermissionError, ValidationError } from '../../../shared/errors/auth.errors';
import { hashApiKey } from '../../../shared/utils/argon2.util';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';

export class ApiKeyDomainService {
  constructor(private readonly repo: AuthRepositoryPort) {}

  async generateApiKey(input: CreateApiKeyInput): Promise<{ rawKey: string; keyRecord: ApiKeyRecord }> {
    const validated = CreateApiKeyInputSchema.parse(input);

    const org = await this.repo.getOrganizationById(validated.org_id);
    if (!org) {
      throw new ValidationError(`Invalid organization ID '${validated.org_id}': Target organization does not exist in the system.`);
    }

    let prefix: string = AUTH_CONSTANTS.API_KEY_PREFIX_GENERAL;
    if (validated.key_type === AUTH_CONSTANTS.KEY_TYPE_SUPER_SECRET) {
      prefix = AUTH_CONSTANTS.API_KEY_PREFIX_SUPER_SECRET;
    } else if (validated.key_type === AUTH_CONSTANTS.KEY_TYPE_TESTING) {
      prefix = AUTH_CONSTANTS.API_KEY_PREFIX_TESTING;
    }

    const keyId = `key_${Math.random().toString(36).substring(2, 9)}`;
    const secret = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    const rawKey = `${prefix}${validated.org_id}_${secret}`;
    const keyHash = await hashApiKey(rawKey);

    const keyRecord: ApiKeyRecord = {
      key_id: keyId,
      org_id: validated.org_id,
      key_type: validated.key_type,
      key_hash: keyHash,
      prefix,
      name: validated.name,
      permissions: validated.permissions,
      created_at_ms: Date.now(),
      revoked: false,
    };

    await this.repo.saveApiKey(keyRecord);
    return { rawKey, keyRecord };
  }

  async listApiKeys(orgId: string): Promise<ApiKeyRecord[]> {
    return this.repo.listApiKeysByOrgId(orgId);
  }

  async verifyApiKey(input: VerifyApiKeyInput): Promise<{ valid: boolean; record: ApiKeyRecord; authorized: boolean }> {
    const validated = VerifyApiKeyInputSchema.parse(input);
    const keyHash = await hashApiKey(validated.key);
    const record = await this.repo.findApiKeyByHash(keyHash);

    if (!record || record.revoked) {
      throw new ApiKeyRevokedError();
    }

    let authorized = true;
    if (validated.required_permission) {
      const isSuperSecret = record.key_type === AUTH_CONSTANTS.KEY_TYPE_SUPER_SECRET;
      const hasAdminAll = record.permissions.includes(AUTH_CONSTANTS.PERMISSION_ADMIN_ALL);
      const hasSpecific = record.permissions.includes(validated.required_permission);
      authorized = isSuperSecret || hasAdminAll || hasSpecific;

      if (!authorized) {
        throw new InsufficientPermissionError(validated.required_permission);
      }
    }

    return { valid: true, record, authorized };
  }

  async revokeApiKey(keyId: string): Promise<void> {
    await this.repo.revokeApiKey(keyId);
  }

  getSystemPermissions(): string[] {
    return [
      AUTH_CONSTANTS.PERMISSION_TRACES_READ,
      AUTH_CONSTANTS.PERMISSION_TRACES_WRITE,
      AUTH_CONSTANTS.PERMISSION_METRICS_READ,
      AUTH_CONSTANTS.PERMISSION_METRICS_WRITE,
      AUTH_CONSTANTS.PERMISSION_LOGS_READ,
      AUTH_CONSTANTS.PERMISSION_LOGS_WRITE,
      AUTH_CONSTANTS.PERMISSION_ALERTS_READ,
      AUTH_CONSTANTS.PERMISSION_ALERTS_WRITE,
      AUTH_CONSTANTS.PERMISSION_ADMIN_ALL,
    ];
  }
}
