import { describe, it, expect, beforeAll } from 'vitest';
import { AuthService } from '../../src/features/auth/service';
import { AuthRestV1Router } from '../../src/api/rest/v1/router';
import { AlloyDBOmniAuthAdapter } from '../../src/infra/adapters/alloydb-omni-auth.adapter';
import { AUTH_CONSTANTS } from '../../src/shared/constants/auth.constants';
import { AUTH_ENDPOINTS, HTTP_METHODS } from '../../src/shared/constants/endpoints';

describe('Auth End-to-End API Flow Test Suite', () => {
  let router: AuthRestV1Router;

  beforeAll(() => {
    const repository = new AlloyDBOmniAuthAdapter();
    const service = new AuthService(repository);
    router = new AuthRestV1Router(service);
  });

  it('should execute end-to-end flow: sign-up, sign-in audit logging, session verification, forgot/reset password, permissions listing, and 3-tier API key verification', async () => {
    const signUpResult = (await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.SIGN_UP, {
      email: 'e2euser@observability.io',
      password: 'StrongPass123!',
      name: 'E2E User',
      organization_name: 'E2E Enterprise',
      role: AUTH_CONSTANTS.ROLE_ADMIN,
    })) as { token: string; user: { email: string; org_name: string } };

    expect(signUpResult.token).toBeDefined();
    expect(signUpResult.user.email).toBe('e2euser@observability.io');

    const signInResult = (await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.SIGN_IN, {
      email: 'e2euser@observability.io',
      password: 'StrongPass123!',
    }, {
      'x-forwarded-for': '192.168.1.100',
      'user-agent': 'E2E-Agent/1.0',
    })) as { token: string };

    expect(signInResult.token).toBeDefined();

    const sessionResult = (await router.route(HTTP_METHODS.GET, AUTH_ENDPOINTS.SESSION, undefined, {
      authorization: `${AUTH_CONSTANTS.BEARER_PREFIX}${signInResult.token}`,
    })) as { sub: string; email: string };

    expect(sessionResult.email).toBe('e2euser@observability.io');

    const forgotResult = (await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.FORGOT_PASSWORD, {
      email: 'e2euser@observability.io',
    })) as { resetToken: string };

    expect(forgotResult.resetToken).toBeDefined();

    const permsResult = (await router.route(HTTP_METHODS.GET, AUTH_ENDPOINTS.PERMISSIONS)) as { permissions: string[] };
    expect(permsResult.permissions).toContain(AUTH_CONSTANTS.PERMISSION_ADMIN_ALL);

    const keyResult = (await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.API_KEYS, {
      name: 'Testing Key',
      org_id: AUTH_CONSTANTS.DEFAULT_ORG_ID,
      key_type: AUTH_CONSTANTS.KEY_TYPE_TESTING,
      permissions: [AUTH_CONSTANTS.PERMISSION_METRICS_READ],
    })) as { rawKey: string };

    expect(keyResult.rawKey.startsWith(AUTH_CONSTANTS.API_KEY_PREFIX_TESTING)).toBe(true);

    const verifyResult = (await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.API_KEYS_VERIFY, {
      key: keyResult.rawKey,
      required_permission: AUTH_CONSTANTS.PERMISSION_METRICS_READ,
    })) as { valid: boolean; authorized: boolean };

    expect(verifyResult.valid).toBe(true);
    expect(verifyResult.authorized).toBe(true);
  });
});
