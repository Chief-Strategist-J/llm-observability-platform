import type { AuthService } from '../../../features/auth/service';
import { handleSignUp, handleSignIn } from './handlers/auth.handler';
import { handleVerifySession } from './handlers/session.handler';
import { handleForgotPassword, handleResetPassword, handleChangePassword } from './handlers/password.handler';
import { handleCreateApiKey, handleVerifyApiKey, handleListPermissions } from './handlers/api-key.handler';
import { withSpan } from '../../../infra/tracing/tracer';
import { AUTH_ENDPOINTS, HTTP_METHODS } from '../../../shared/constants/endpoints';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';
import { createSuccessResponse, createErrorResponse, type StandardApiResponse } from '../../../shared/errors/error-handler';

export class AuthRestV1Router {
  constructor(private readonly service: AuthService) {}

  async route(method: string, path: string, body?: unknown, headers?: Record<string, string>): Promise<{ statusCode: number; payload: StandardApiResponse<unknown> }> {
    return withSpan(`REST ${method} ${path}`, async (span) => {
      span.setAttribute('http.method', method);
      span.setAttribute('http.target', path);

      try {
        let resultData: unknown = undefined;

        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.SIGN_UP) {
          resultData = await handleSignUp(this.service, body);
          return { statusCode: 201, payload: createSuccessResponse(resultData, 'User and organization successfully registered') };
        }
        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.SIGN_IN) {
          resultData = await handleSignIn(this.service, body, headers);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'User signed in successfully') };
        }
        if (method === HTTP_METHODS.GET && path === AUTH_ENDPOINTS.SESSION) {
          const authHeader = headers?.[AUTH_CONSTANTS.HEADER_AUTHORIZATION] ?? headers?.[AUTH_CONSTANTS.HEADER_AUTHORIZATION_CAMEL];
          resultData = await handleVerifySession(this.service, authHeader);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Session token verified') };
        }
        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.FORGOT_PASSWORD) {
          resultData = await handleForgotPassword(this.service, body);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Password reset request processed') };
        }
        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.RESET_PASSWORD) {
          resultData = await handleResetPassword(this.service, body);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Password successfully reset') };
        }
        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.CHANGE_PASSWORD) {
          const authHeader = headers?.[AUTH_CONSTANTS.HEADER_AUTHORIZATION] ?? headers?.[AUTH_CONSTANTS.HEADER_AUTHORIZATION_CAMEL];
          const payload = await handleVerifySession(this.service, authHeader);
          resultData = await handleChangePassword(this.service, payload.sub, body);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Password successfully changed') };
        }
        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.API_KEYS) {
          resultData = await handleCreateApiKey(this.service, body);
          return { statusCode: 201, payload: createSuccessResponse(resultData, 'API key successfully created') };
        }
        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.API_KEYS_VERIFY) {
          resultData = await handleVerifyApiKey(this.service, body);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'API key verified') };
        }
        if (method === HTTP_METHODS.GET && path === AUTH_ENDPOINTS.PERMISSIONS) {
          resultData = await handleListPermissions(this.service);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'System permissions retrieved') };
        }

        throw new Error(`Route not found: ${method} ${path}`);
      } catch (err: unknown) {
        return createErrorResponse(err);
      }
    });
  }
}
