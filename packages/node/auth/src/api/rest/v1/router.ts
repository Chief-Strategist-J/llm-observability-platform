import type { AuthService } from '../../../features/auth/service';
import {
  handleSignUp,
  handleSignIn,
  handleSignOut,
  handleFetchAuditLogs,
  handleCreateOrganization,
  handleListOrganizations,
  handleGetOrganization,
  handleUpdateOrganization,
  handleDeleteOrganization,
  handleSwitchOrganization,
  handleListUsers,
  handleGetUserById,
  handleGetMyProfile,
  handleUpdateMyProfile,
  handleInviteUser,
  handleUpdateUserRole,
  handleGetUserPermissions,
  handleUpdateUserPermissions,
  handleCreateUser,
  handleBlockUser,
  handleUnblockUser,
  handleDeleteUser,
  handleListApiKeys,
  handleRevokeApiKey,
} from './handlers/auth.handler';
import { handleVerifySession } from './handlers/session.handler';
import { handleForgotPassword, handleResetPassword, handleChangePassword } from './handlers/password.handler';
import { handleCreateApiKey, handleVerifyApiKey, handleListPermissions } from './handlers/api-key.handler';
import { withSpan } from '../../../infra/tracing/tracer';
import { AUTH_ENDPOINTS, HTTP_METHODS } from '../../../shared/constants/endpoints';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';
import { createSuccessResponse, createErrorResponse, type StandardApiResponse } from '../../../shared/errors/error-handler';

export class AuthRestV1Router {
  constructor(private readonly service: AuthService) {}

  async route(method: string, path: string, body?: unknown, headers?: Record<string, string>, queryParams?: Record<string, string>): Promise<{ statusCode: number; payload: StandardApiResponse<unknown> }> {
    return withSpan(`REST ${method} ${path}`, async (span) => {
      span.setAttribute('http.method', method);
      span.setAttribute('http.target', path);

      try {
        const authHeader = headers?.[AUTH_CONSTANTS.HEADERS.AUTHORIZATION] ?? headers?.[AUTH_CONSTANTS.HEADERS.AUTHORIZATION_CAMEL];

        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.SIGN_UP) {
          const resultData = await handleSignUp(this.service, body);
          return { statusCode: 201, payload: createSuccessResponse(resultData, 'User and organization successfully registered') };
        }

        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.SIGN_IN) {
          const resultData = await handleSignIn(this.service, body, headers);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'User signed in successfully') };
        }

        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.SIGN_OUT) {
          await handleSignOut(this.service, authHeader);
          return { statusCode: 200, payload: createSuccessResponse(null, 'Signed out successfully') };
        }

        if (method === HTTP_METHODS.GET && path === AUTH_ENDPOINTS.SESSION) {
          const resultData = await handleVerifySession(this.service, authHeader);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Session token verified') };
        }

        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.FORGOT_PASSWORD) {
          const resultData = await handleForgotPassword(this.service, body);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Password reset request processed') };
        }

        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.RESET_PASSWORD) {
          const resultData = await handleResetPassword(this.service, body);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Password successfully reset') };
        }

        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.CHANGE_PASSWORD) {
          const session = await handleVerifySession(this.service, authHeader);
          const resultData = await handleChangePassword(this.service, session.sub, body);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Password successfully changed') };
        }

        if (method === HTTP_METHODS.GET && path === AUTH_ENDPOINTS.ORGANIZATIONS) {
          const session = await handleVerifySession(this.service, authHeader);
          const resultData = await handleListOrganizations(this.service, session.sub);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Organizations retrieved') };
        }

        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.ORGANIZATIONS) {
          const session = await handleVerifySession(this.service, authHeader);
          const resultData = await handleCreateOrganization(this.service, body, session.sub);
          return { statusCode: 201, payload: createSuccessResponse(resultData, 'Organization created successfully') };
        }

        if (method === HTTP_METHODS.GET && path.startsWith(`${AUTH_ENDPOINTS.ORGANIZATIONS}/`) && !path.includes('/switch')) {
          const orgId = path.substring(`${AUTH_ENDPOINTS.ORGANIZATIONS}/`.length);
          const resultData = await handleGetOrganization(this.service, orgId);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Organization retrieved') };
        }

        if (method === HTTP_METHODS.PATCH && path.startsWith(`${AUTH_ENDPOINTS.ORGANIZATIONS}/`) && !path.includes('/switch')) {
          const orgId = path.substring(`${AUTH_ENDPOINTS.ORGANIZATIONS}/`.length);
          const resultData = await handleUpdateOrganization(this.service, orgId, body);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Organization updated') };
        }

        if (method === HTTP_METHODS.DELETE && path.startsWith(`${AUTH_ENDPOINTS.ORGANIZATIONS}/`) && !path.includes('/switch')) {
          const orgId = path.substring(`${AUTH_ENDPOINTS.ORGANIZATIONS}/`.length);
          const resultData = await handleDeleteOrganization(this.service, orgId);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Organization soft-deleted with 30-day backup retention') };
        }

        if (method === HTTP_METHODS.POST && path.startsWith(`${AUTH_ENDPOINTS.ORGANIZATIONS}/`) && path.endsWith('/switch')) {
          const session = await handleVerifySession(this.service, authHeader);
          const orgId = path.substring(`${AUTH_ENDPOINTS.ORGANIZATIONS}/`.length, path.length - '/switch'.length);
          const token = authHeader?.replace('Bearer ', '') ?? '';
          const resultData = await handleSwitchOrganization(this.service, session.sub, orgId, token);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Organization context switched') };
        }

        if (method === HTTP_METHODS.GET && path === AUTH_ENDPOINTS.USERS_ME) {
          const session = await handleVerifySession(this.service, authHeader);
          const resultData = await handleGetMyProfile(this.service, session.sub);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'User profile retrieved') };
        }

        if (method === HTTP_METHODS.PATCH && path === AUTH_ENDPOINTS.USERS_ME) {
          const session = await handleVerifySession(this.service, authHeader);
          const resultData = await handleUpdateMyProfile(this.service, session.sub, body);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'User profile updated') };
        }

        if (method === HTTP_METHODS.GET && path === AUTH_ENDPOINTS.USERS) {
          const session = await handleVerifySession(this.service, authHeader);
          const resultData = await handleListUsers(this.service, session.org.org_id);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Members retrieved') };
        }

        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.USERS) {
          const resultData = await handleCreateUser(this.service, body);
          return { statusCode: 201, payload: createSuccessResponse(resultData, 'User created in target organization with specific permissions') };
        }

        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.USERS_INVITE) {
          const session = await handleVerifySession(this.service, authHeader);
          const resultData = await handleInviteUser(this.service, body, session.org.org_id, session.org.org_name);
          return { statusCode: 201, payload: createSuccessResponse(resultData, 'User invited to organization') };
        }

        if (method === HTTP_METHODS.POST && path.startsWith(`${AUTH_ENDPOINTS.USERS}/`) && path.endsWith('/block')) {
          const userId = path.substring(`${AUTH_ENDPOINTS.USERS}/`.length, path.length - '/block'.length);
          const resultData = await handleBlockUser(this.service, userId);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'User blocked successfully') };
        }

        if (method === HTTP_METHODS.DELETE && path.startsWith(`${AUTH_ENDPOINTS.USERS}/`) && path.endsWith('/unblock')) {
          const userId = path.substring(`${AUTH_ENDPOINTS.USERS}/`.length, path.length - '/unblock'.length);
          const resultData = await handleUnblockUser(this.service, userId);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'User unblocked successfully') };
        }

        if (method === HTTP_METHODS.PATCH && path.startsWith(`${AUTH_ENDPOINTS.USERS}/`) && path.endsWith('/role')) {
          const userId = path.substring(`${AUTH_ENDPOINTS.USERS}/`.length, path.length - '/role'.length);
          await handleUpdateUserRole(this.service, userId, body);
          return { statusCode: 200, payload: createSuccessResponse(null, 'User role updated') };
        }

        if (method === HTTP_METHODS.GET && path.startsWith(`${AUTH_ENDPOINTS.USERS}/`) && path.endsWith('/permissions')) {
          const userId = path.substring(`${AUTH_ENDPOINTS.USERS}/`.length, path.length - '/permissions'.length);
          const resultData = await handleGetUserPermissions(this.service, userId);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'User permissions retrieved') };
        }

        if (method === HTTP_METHODS.PATCH && path.startsWith(`${AUTH_ENDPOINTS.USERS}/`) && path.endsWith('/permissions')) {
          const userId = path.substring(`${AUTH_ENDPOINTS.USERS}/`.length, path.length - '/permissions'.length);
          await handleUpdateUserPermissions(this.service, userId, body);
          return { statusCode: 200, payload: createSuccessResponse(null, 'User permissions updated') };
        }

        if (method === HTTP_METHODS.GET && path.startsWith(`${AUTH_ENDPOINTS.USERS}/`)) {
          const userId = path.substring(`${AUTH_ENDPOINTS.USERS}/`.length);
          const resultData = await handleGetUserById(this.service, userId);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'User retrieved') };
        }

        if (method === HTTP_METHODS.DELETE && path.startsWith(`${AUTH_ENDPOINTS.USERS}/`)) {
          const userId = path.substring(`${AUTH_ENDPOINTS.USERS}/`.length);
          const resultData = await handleDeleteUser(this.service, userId);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'User soft-deleted with 30-day backup retention') };
        }

        if (method === HTTP_METHODS.GET && path === AUTH_ENDPOINTS.API_KEYS) {
          const session = await handleVerifySession(this.service, authHeader);
          const resultData = await handleListApiKeys(this.service, session.org.org_id);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'API keys retrieved') };
        }

        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.API_KEYS) {
          const resultData = await handleCreateApiKey(this.service, body);
          return { statusCode: 201, payload: createSuccessResponse(resultData, 'API key successfully created') };
        }

        if (method === HTTP_METHODS.POST && path === AUTH_ENDPOINTS.API_KEYS_VERIFY) {
          const resultData = await handleVerifyApiKey(this.service, body);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'API key verified') };
        }

        if (method === HTTP_METHODS.POST && path.startsWith(`${AUTH_ENDPOINTS.API_KEYS}/`) && path.endsWith('/revoke')) {
          const keyId = path.substring(`${AUTH_ENDPOINTS.API_KEYS}/`.length, path.length - '/revoke'.length);
          await handleRevokeApiKey(this.service, keyId);
          return { statusCode: 200, payload: createSuccessResponse(null, 'API key revoked') };
        }

        if (method === HTTP_METHODS.GET && path === AUTH_ENDPOINTS.PERMISSIONS) {
          const resultData = await handleListPermissions(this.service);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'System permissions retrieved') };
        }

        if (method === HTTP_METHODS.GET && path === AUTH_ENDPOINTS.AUDIT_LOGS) {
          const session = await handleVerifySession(this.service, authHeader);
          const resultData = await handleFetchAuditLogs(this.service, session.sub, queryParams);
          return { statusCode: 200, payload: createSuccessResponse(resultData, 'Audit logs retrieved') };
        }

        throw new Error(`Route not found: ${method} ${path}`);
      } catch (err: unknown) {
        return createErrorResponse(err);
      }
    });
  }
}
