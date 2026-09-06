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
import { AUTH_ENDPOINTS, HTTP_METHODS } from '../../../shared/constants/endpoints';

export interface RouteContext {
  service: AuthService;
  body?: any;
  headers?: Record<string, string>;
  queryParams?: Record<string, string>;
  authHeader?: string;
  params: Record<string, string>;
}

export interface RouteRule {
  name: string;
  method: string;
  pattern: string;
  requiresAuth?: boolean;
  successStatus?: number;
  successMessage: string;
  handler: (ctx: RouteContext, session?: any) => Promise<any>;
}

export const ROUTE_RULES: RouteRule[] = [
  {
    name: 'root_check',
    method: HTTP_METHODS.GET,
    pattern: '/',
    successMessage: 'Auth Service API v1 is live',
    handler: async () => ({ service: 'auth-service', version: '1.0.0', status: 'healthy' }),
  },
  {
    name: 'health_check',
    method: HTTP_METHODS.GET,
    pattern: '/health',
    successMessage: 'Auth service is healthy',
    handler: async () => ({ status: 'ok' }),
  },
  {
    name: 'health_check_v1',
    method: HTTP_METHODS.GET,
    pattern: '/api/v1/auth/health',
    successMessage: 'Auth service is healthy',
    handler: async () => ({ status: 'ok' }),
  },
  {
    name: 'sign_up',
    method: HTTP_METHODS.POST,
    pattern: AUTH_ENDPOINTS.SIGN_UP,
    successStatus: 201,
    successMessage: 'User and organization successfully registered',
    handler: (ctx) => handleSignUp(ctx.service, ctx.body),
  },
  {
    name: 'sign_in',
    method: HTTP_METHODS.POST,
    pattern: AUTH_ENDPOINTS.SIGN_IN,
    successMessage: 'User signed in successfully',
    handler: (ctx) => handleSignIn(ctx.service, ctx.body, ctx.headers),
  },
  {
    name: 'sign_out',
    method: HTTP_METHODS.POST,
    pattern: AUTH_ENDPOINTS.SIGN_OUT,
    successMessage: 'Signed out successfully',
    handler: async (ctx) => {
      await handleSignOut(ctx.service, ctx.authHeader);
      return null;
    },
  },
  {
    name: 'verify_session',
    method: HTTP_METHODS.GET,
    pattern: AUTH_ENDPOINTS.SESSION,
    successMessage: 'Session token verified',
    handler: (ctx) => handleVerifySession(ctx.service, ctx.authHeader),
  },
  {
    name: 'forgot_password',
    method: HTTP_METHODS.POST,
    pattern: AUTH_ENDPOINTS.FORGOT_PASSWORD,
    successMessage: 'Password reset request processed',
    handler: (ctx) => handleForgotPassword(ctx.service, ctx.body),
  },
  {
    name: 'reset_password',
    method: HTTP_METHODS.POST,
    pattern: AUTH_ENDPOINTS.RESET_PASSWORD,
    successMessage: 'Password successfully reset',
    handler: (ctx) => handleResetPassword(ctx.service, ctx.body),
  },
  {
    name: 'change_password',
    method: HTTP_METHODS.POST,
    pattern: AUTH_ENDPOINTS.CHANGE_PASSWORD,
    requiresAuth: true,
    successMessage: 'Password successfully changed',
    handler: (ctx, session) => handleChangePassword(ctx.service, session.sub, ctx.body),
  },
  {
    name: 'list_organizations',
    method: HTTP_METHODS.GET,
    pattern: AUTH_ENDPOINTS.ORGANIZATIONS,
    requiresAuth: true,
    successMessage: 'Organizations retrieved',
    handler: (ctx, session) => handleListOrganizations(ctx.service, session.sub),
  },
  {
    name: 'create_organization',
    method: HTTP_METHODS.POST,
    pattern: AUTH_ENDPOINTS.ORGANIZATIONS,
    requiresAuth: true,
    successStatus: 201,
    successMessage: 'Organization created successfully',
    handler: (ctx, session) => handleCreateOrganization(ctx.service, ctx.body, session.sub),
  },
  {
    name: 'switch_organization',
    method: HTTP_METHODS.POST,
    pattern: `${AUTH_ENDPOINTS.ORGANIZATIONS}/:id/switch`,
    requiresAuth: true,
    successMessage: 'Organization context switched',
    handler: (ctx, session) => {
      const token = ctx.authHeader?.replace('Bearer ', '') ?? '';
      return handleSwitchOrganization(ctx.service, session.sub, ctx.params['id']!, token);
    },
  },
  {
    name: 'get_organization',
    method: HTTP_METHODS.GET,
    pattern: `${AUTH_ENDPOINTS.ORGANIZATIONS}/:id`,
    successMessage: 'Organization retrieved',
    handler: (ctx) => handleGetOrganization(ctx.service, ctx.params['id']!),
  },
  {
    name: 'update_organization',
    method: HTTP_METHODS.PATCH,
    pattern: `${AUTH_ENDPOINTS.ORGANIZATIONS}/:id`,
    successMessage: 'Organization updated',
    handler: (ctx) => handleUpdateOrganization(ctx.service, ctx.params['id']!, ctx.body),
  },
  {
    name: 'delete_organization',
    method: HTTP_METHODS.DELETE,
    pattern: `${AUTH_ENDPOINTS.ORGANIZATIONS}/:id`,
    successMessage: 'Organization soft-deleted with 30-day backup retention',
    handler: (ctx) => handleDeleteOrganization(ctx.service, ctx.params['id']!),
  },
  {
    name: 'get_my_profile',
    method: HTTP_METHODS.GET,
    pattern: AUTH_ENDPOINTS.USERS_ME,
    requiresAuth: true,
    successMessage: 'User profile retrieved',
    handler: (ctx, session) => handleGetMyProfile(ctx.service, session.sub),
  },
  {
    name: 'update_my_profile',
    method: HTTP_METHODS.PATCH,
    pattern: AUTH_ENDPOINTS.USERS_ME,
    requiresAuth: true,
    successMessage: 'User profile updated',
    handler: (ctx, session) => handleUpdateMyProfile(ctx.service, session.sub, ctx.body),
  },
  {
    name: 'list_users',
    method: HTTP_METHODS.GET,
    pattern: AUTH_ENDPOINTS.USERS,
    requiresAuth: true,
    successMessage: 'Members retrieved',
    handler: (ctx, session) => handleListUsers(ctx.service, session.org.org_id),
  },
  {
    name: 'create_user',
    method: HTTP_METHODS.POST,
    pattern: AUTH_ENDPOINTS.USERS,
    successStatus: 201,
    successMessage: 'User created in target organization with specific permissions',
    handler: (ctx) => handleCreateUser(ctx.service, ctx.body),
  },
  {
    name: 'invite_user',
    method: HTTP_METHODS.POST,
    pattern: AUTH_ENDPOINTS.USERS_INVITE,
    requiresAuth: true,
    successStatus: 201,
    successMessage: 'User invited to organization',
    handler: (ctx, session) => handleInviteUser(ctx.service, ctx.body, session.org.org_id, session.org.org_name),
  },
  {
    name: 'block_user',
    method: HTTP_METHODS.POST,
    pattern: `${AUTH_ENDPOINTS.USERS}/:id/block`,
    successMessage: 'User blocked successfully',
    handler: (ctx) => handleBlockUser(ctx.service, ctx.params['id']!),
  },
  {
    name: 'unblock_user',
    method: HTTP_METHODS.DELETE,
    pattern: `${AUTH_ENDPOINTS.USERS}/:id/unblock`,
    successMessage: 'User unblocked successfully',
    handler: (ctx) => handleUnblockUser(ctx.service, ctx.params['id']!),
  },
  {
    name: 'update_user_role',
    method: HTTP_METHODS.PATCH,
    pattern: `${AUTH_ENDPOINTS.USERS}/:id/role`,
    successMessage: 'User role updated',
    handler: async (ctx) => {
      await handleUpdateUserRole(ctx.service, ctx.params['id']!, ctx.body);
      return null;
    },
  },
  {
    name: 'get_user_permissions',
    method: HTTP_METHODS.GET,
    pattern: `${AUTH_ENDPOINTS.USERS}/:id/permissions`,
    successMessage: 'User permissions retrieved',
    handler: (ctx) => handleGetUserPermissions(ctx.service, ctx.params['id']!),
  },
  {
    name: 'update_user_permissions',
    method: HTTP_METHODS.PATCH,
    pattern: `${AUTH_ENDPOINTS.USERS}/:id/permissions`,
    successMessage: 'User permissions updated',
    handler: async (ctx) => {
      await handleUpdateUserPermissions(ctx.service, ctx.params['id']!, ctx.body);
      return null;
    },
  },
  {
    name: 'get_user_by_id',
    method: HTTP_METHODS.GET,
    pattern: `${AUTH_ENDPOINTS.USERS}/:id`,
    successMessage: 'User retrieved',
    handler: (ctx) => handleGetUserById(ctx.service, ctx.params['id']!),
  },
  {
    name: 'delete_user',
    method: HTTP_METHODS.DELETE,
    pattern: `${AUTH_ENDPOINTS.USERS}/:id`,
    successMessage: 'User soft-deleted with 30-day backup retention',
    handler: (ctx) => handleDeleteUser(ctx.service, ctx.params['id']!),
  },
  {
    name: 'list_api_keys',
    method: HTTP_METHODS.GET,
    pattern: AUTH_ENDPOINTS.API_KEYS,
    requiresAuth: true,
    successMessage: 'API keys retrieved',
    handler: (ctx, session) => handleListApiKeys(ctx.service, session.org.org_id),
  },
  {
    name: 'create_api_key',
    method: HTTP_METHODS.POST,
    pattern: AUTH_ENDPOINTS.API_KEYS,
    successStatus: 201,
    successMessage: 'API key successfully created',
    handler: (ctx) => handleCreateApiKey(ctx.service, ctx.body),
  },
  {
    name: 'verify_api_key',
    method: HTTP_METHODS.POST,
    pattern: AUTH_ENDPOINTS.API_KEYS_VERIFY,
    successMessage: 'API key verified',
    handler: (ctx) => handleVerifyApiKey(ctx.service, ctx.body),
  },
  {
    name: 'revoke_api_key',
    method: HTTP_METHODS.POST,
    pattern: `${AUTH_ENDPOINTS.API_KEYS}/:id/revoke`,
    successMessage: 'API key revoked',
    handler: async (ctx) => {
      await handleRevokeApiKey(ctx.service, ctx.params['id']!);
      return null;
    },
  },
  {
    name: 'list_permissions',
    method: HTTP_METHODS.GET,
    pattern: AUTH_ENDPOINTS.PERMISSIONS,
    successMessage: 'System permissions retrieved',
    handler: (ctx) => handleListPermissions(ctx.service),
  },
  {
    name: 'fetch_audit_logs',
    method: HTTP_METHODS.GET,
    pattern: AUTH_ENDPOINTS.AUDIT_LOGS,
    requiresAuth: true,
    successMessage: 'Audit logs retrieved',
    handler: (ctx, session) => handleFetchAuditLogs(ctx.service, session.sub, ctx.queryParams),
  },
];
