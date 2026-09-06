import { describe, it, expect, beforeAll } from 'vitest';
import { AuthService } from '../../src/features/auth/service';
import { AuthRestV1Router } from '../../src/api/rest/v1/router';
import { AlloyDBOmniAuthAdapter } from '../../src/infra/adapters/postgres/alloydb-omni-auth.adapter';
import { AUTH_CONSTANTS } from '../../src/shared/constants/auth.constants';
import { AUTH_ENDPOINTS, HTTP_METHODS } from '../../src/shared/constants/endpoints';

describe('Auth End-to-End API Flow Test Suite', () => {
  let router: AuthRestV1Router;

  beforeAll(() => {
    const repository = new AlloyDBOmniAuthAdapter();
    const service = new AuthService(repository);
    router = new AuthRestV1Router(service);
  });

  it('should execute end-to-end flow with standardized response envelope (status, message, data, error)', async () => {
    const signUpRes = await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.SIGN_UP, {
      email: 'e2euser@observability.io',
      password: 'StrongPass123!',
      name: 'E2E User',
      organization_name: 'E2E Enterprise',
      role: AUTH_CONSTANTS.ROLE_ADMIN,
    });

    expect(signUpRes.statusCode).toBe(201);
    expect(signUpRes.payload.status).toBe('success');
    const signUpData = signUpRes.payload.data as { token: string; user: { email: string } };
    expect(signUpData.token).toBeDefined();
    expect(signUpData.user.email).toBe('e2euser@observability.io');

    const signInRes = await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.SIGN_IN, {
      email: 'e2euser@observability.io',
      password: 'StrongPass123!',
    }, {
      'x-forwarded-for': '192.168.1.100',
      'user-agent': 'E2E-Agent/1.0',
    });

    expect(signInRes.statusCode).toBe(200);
    expect(signInRes.payload.status).toBe('success');
    const signInData = signInRes.payload.data as { token: string };
    expect(signInData.token).toBeDefined();

    const sessionRes = await router.route(HTTP_METHODS.GET, AUTH_ENDPOINTS.SESSION, undefined, {
      authorization: `${AUTH_CONSTANTS.HEADERS.BEARER_PREFIX}${signInData.token}`,
    });

    expect(sessionRes.statusCode).toBe(200);
    const sessionData = sessionRes.payload.data as { email: string };
    expect(sessionData.email).toBe('e2euser@observability.io');

    const forgotRes = await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.FORGOT_PASSWORD, {
      email: 'e2euser@observability.io',
    });

    expect(forgotRes.statusCode).toBe(200);
    const forgotData = forgotRes.payload.data as { resetToken: string };
    expect(forgotData.resetToken).toBeDefined();

    const permsRes = await router.route(HTTP_METHODS.GET, AUTH_ENDPOINTS.PERMISSIONS);
    expect(permsRes.statusCode).toBe(200);
    const permsData = permsRes.payload.data as { permissions: string[] };
    expect(permsData.permissions).toContain(AUTH_CONSTANTS.PERMISSION_ADMIN_ALL);

    const keyRes = await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.API_KEYS, {
      name: 'Testing Key',
      org_id: AUTH_CONSTANTS.DEFAULT_ORG_ID,
      key_type: AUTH_CONSTANTS.KEY_TYPE_TESTING,
      permissions: [AUTH_CONSTANTS.PERMISSION_METRICS_READ],
    });

    expect(keyRes.statusCode).toBe(201);
    const keyData = keyRes.payload.data as { rawKey: string };
    expect(keyData.rawKey.startsWith(AUTH_CONSTANTS.API_KEY_PREFIX_TESTING)).toBe(true);

    const verifyRes = await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.API_KEYS_VERIFY, {
      key: keyData.rawKey,
      required_permission: AUTH_CONSTANTS.PERMISSION_METRICS_READ,
    });

    expect(verifyRes.statusCode).toBe(200);
    const verifyData = verifyRes.payload.data as { valid: boolean; authorized: boolean };
    expect(verifyData.valid).toBe(true);
    expect(verifyData.authorized).toBe(true);
  });
});
