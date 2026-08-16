import type { AuthService } from '../../../../features/auth/service';
import { CreateApiKeyInputSchema } from '../../../../features/auth/types';
import type { ApiKeyRecord } from '../../../../shared/types/auth.types';

export async function handleCreateApiKey(service: AuthService, body: unknown): Promise<{ rawKey: string; keyRecord: ApiKeyRecord }> {
  const parsed = CreateApiKeyInputSchema.parse(body);
  return service.generateApiKey(parsed);
}

export async function handleVerifyApiKey(service: AuthService, rawKey: string): Promise<ApiKeyRecord> {
  return service.verifyApiKey(rawKey);
}
