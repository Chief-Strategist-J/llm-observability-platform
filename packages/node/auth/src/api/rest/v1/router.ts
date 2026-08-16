import type { AuthService } from '../../../features/auth/service';
import { handleSignIn } from './handlers/auth.handler';
import { handleVerifySession } from './handlers/session.handler';
import { handleCreateApiKey, handleVerifyApiKey } from './handlers/api-key.handler';

export class AuthRestV1Router {
  constructor(private readonly service: AuthService) {}

  async route(method: string, path: string, body?: unknown, headers?: Record<string, string>): Promise<unknown> {
    if (method === 'POST' && path === '/api/v1/auth/sign-in') {
      return handleSignIn(this.service, body);
    }
    if (method === 'GET' && path === '/api/v1/auth/session') {
      return handleVerifySession(this.service, headers?.['authorization'] ?? headers?.['Authorization']);
    }
    if (method === 'POST' && path === '/api/v1/auth/api-keys') {
      return handleCreateApiKey(this.service, body);
    }
    if (method === 'POST' && path === '/api/v1/auth/api-keys/verify') {
      const rawKey = (body as { key?: string } | undefined)?.key ?? '';
      return handleVerifyApiKey(this.service, rawKey);
    }
    throw new Error(`Route not found: ${method} ${path}`);
  }
}
