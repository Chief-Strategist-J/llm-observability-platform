import type { AuthService } from '../../../../features/auth/service';
import type { CreateApiKeyInput, VerifyApiKeyInput } from '../../../../features/auth/types';

export async function handleCreateApiKey(service: AuthService, body: unknown): Promise<unknown> {
  const input = body as CreateApiKeyInput;
  return service.generateApiKey(input);
}

export async function handleVerifyApiKey(service: AuthService, body: unknown): Promise<unknown> {
  const input = body as VerifyApiKeyInput;
  return service.verifyApiKey(input);
}

export async function handleListPermissions(service: AuthService): Promise<unknown> {
  return { permissions: service.getSystemPermissions() };
}
