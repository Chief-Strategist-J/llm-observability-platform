import type { AuthService } from '../../../features/auth/service';
import { handleSignUp, handleSignIn } from './handlers/auth.handler';
import { handleVerifySession } from './handlers/session.handler';
import { handleForgotPassword, handleResetPassword, handleChangePassword } from './handlers/password.handler';
import { handleCreateApiKey, handleVerifyApiKey, handleListPermissions } from './handlers/api-key.handler';
import { withSpan } from '../../../infra/tracing/tracer';
import { AUTH_ENDPOINTS, HTTP_METHODS } from '../../../shared/constants/endpoints';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';

export class AuthRestV1Router {
  constructor(private readonly service: AuthService) {}

  async route(method: string, path: string, body?: unknown, headers?: Record<string, string>): Promise<unknown> {
    return withSpan(`REST ${method} ${path}`, async (span) => {
      span.setAttribute('http.method', method);
      span.setAttribute('http.target', path);

      if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.SIGN_UP) {
        return handleSignUp(this.service, body);
      }
      if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.SIGN_IN) {
        return handleSignIn(this.service, body, headers);
      }
      if (method === HTTP_METHODS.GET && path === AUTH_ENDPOINTS.SESSION) {
        const authHeader = headers?.[AUTH_CONSTANTS.HEADER_AUTHORIZATION] ?? headers?.[AUTH_CONSTANTS.HEADER_AUTHORIZATION_CAMEL];
        return handleVerifySession(this.service, authHeader);
      }
      if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.FORGOT_PASSWORD) {
        return handleForgotPassword(this.service, body);
      }
      if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.RESET_PASSWORD) {
        return handleResetPassword(this.service, body);
      }
      if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.CHANGE_PASSWORD) {
        const authHeader = headers?.[AUTH_CONSTANTS.HEADER_AUTHORIZATION] ?? headers?.[AUTH_CONSTANTS.HEADER_AUTHORIZATION_CAMEL];
        const payload = await handleVerifySession(this.service, authHeader);
        return handleChangePassword(this.service, payload.sub, body);
      }
      if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.API_KEYS) {
        return handleCreateApiKey(this.service, body);
      }
      if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.API_KEYS_VERIFY) {
        return handleVerifyApiKey(this.service, body);
      }
      if (method === HTTP_METHODS.GET && path === AUTH_ENDPOINTS.PERMISSIONS) {
        return handleListPermissions(this.service);
      }
      throw new Error(`Route not found: ${method} ${path}`);
    });
  }
}
