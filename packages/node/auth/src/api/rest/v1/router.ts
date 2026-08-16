import type { AuthService } from '../../../features/auth/service';
import { handleSignIn } from './handlers/auth.handler';
import { handleVerifySession } from './handlers/session.handler';
import { handleCreateApiKey, handleVerifyApiKey } from './handlers/api-key.handler';
import { withSpan } from '../../../infra/tracing/tracer';
import { AUTH_ENDPOINTS, HTTP_METHODS } from '../../../shared/constants/endpoints';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';

export class AuthRestV1Router {
  constructor(private readonly service: AuthService) {}

  async route(method: string, path: string, body?: unknown, headers?: Record<string, string>): Promise<unknown> {
    return withSpan(`REST ${method} ${path}`, async (span) => {
      span.setAttribute('http.method', method);
      span.setAttribute('http.target', path);

      if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.SIGN_IN) {
        return handleSignIn(this.service, body);
      }
      if (method === HTTP_METHODS.GET && path === AUTH_ENDPOINTS.SESSION) {
        const authHeader = headers?.[AUTH_CONSTANTS.HEADER_AUTHORIZATION] ?? headers?.[AUTH_CONSTANTS.HEADER_AUTHORIZATION_CAMEL];
        return handleVerifySession(this.service, authHeader);
      }
      if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.API_KEYS) {
        return handleCreateApiKey(this.service, body);
      }
      if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.API_KEYS_VERIFY) {
        const rawKey = (body as { key?: string } | undefined)?.key ?? '';
        return handleVerifyApiKey(this.service, rawKey);
      }
      throw new Error(`Route not found: ${method} ${path}`);
    });
  }
}
