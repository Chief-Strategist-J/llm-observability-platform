import { AuthService } from '../../src/features/auth/service';
import { AuthRestV1Router } from '../../src/api/rest/v1/router';
import { AlloyDBOmniAuthAdapter } from '../../src/infra/adapters/alloydb-omni-auth.adapter';
import { RedisSessionAdapter } from '../../src/infra/adapters/redis-session.adapter';
import { AUTH_CONSTANTS } from '../../src/shared/constants/auth.constants';
import { AUTH_ENDPOINTS, HTTP_METHODS } from '../../src/shared/constants/endpoints';

describe('Auth End-to-End API Flow', () => {
  let router: AuthRestV1Router;

  beforeAll(() => {
    const repository = new AlloyDBOmniAuthAdapter();
    const sessionAdapter = new RedisSessionAdapter();
    const service = new AuthService(repository, sessionAdapter);
    router = new AuthRestV1Router(service);
  });

  it('should execute complete user sign-in, session verification, and API key generation flow', async () => {
    const loginResult = (await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.SIGN_IN, {
      email: AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL,
      password: 'password123',
    })) as { token: string; payload: { email: string } };

    expect(loginResult.token).toBeDefined();
    expect(loginResult.payload.email).toBe(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL);

    const sessionResult = (await router.route(HTTP_METHODS.GET, AUTH_ENDPOINTS.SESSION, undefined, {
      authorization: `${AUTH_CONSTANTS.BEARER_PREFIX}${loginResult.token}`,
    })) as { email: string };

    expect(sessionResult.email).toBe(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL);

    const keyResult = (await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.API_KEYS, {
      name: 'E2E Key',
      org_id: AUTH_CONSTANTS.DEFAULT_ORG_ID,
    })) as { rawKey: string };

    expect(keyResult.rawKey).toBeDefined();
    expect(keyResult.rawKey.startsWith(AUTH_CONSTANTS.API_KEY_PREFIX)).toBe(true);

    const verifyResult = (await router.route(HTTP_METHODS.POST, AUTH_ENDPOINTS.API_KEYS_VERIFY, {
      key: keyResult.rawKey,
    })) as { key_id: string };

    expect(verifyResult.key_id).toBeDefined();
  });
});
