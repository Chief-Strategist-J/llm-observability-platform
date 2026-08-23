import { describe, it, expect, beforeEach } from 'vitest';
import { AlloyDBOmniAuthAdapter } from '../../src/infra/adapters/postgres/alloydb-omni-auth.adapter';
import { AuthService } from '../../src/features/auth/service';
import { AuthRestV1Router } from '../../src/api/rest/v1/router';
import { AUTH_CONSTANTS } from '../../src/shared/constants/auth.constants';

describe('Hexagonal Ports & Adapters Architecture Unit Tests', () => {
  let dbAdapter: AlloyDBOmniAuthAdapter;
  let service: AuthService;
  let router: AuthRestV1Router;

  beforeEach(() => {
    dbAdapter = new AlloyDBOmniAuthAdapter();
    service = new AuthService(dbAdapter);
    router = new AuthRestV1Router(service);
  });

  it('should flow sign-in request through Router and Service to Database Adapter', async () => {
    const signInResult = await service.signIn({
      email: AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL,
      password: 'password123',
      ip_address: '127.0.0.1',
      user_agent: 'VitestHexagonal/1.0',
    });

    expect(signInResult.token).toBeDefined();
    expect(signInResult.payload.email).toBe(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL);
    expect(signInResult.user.role).toBe(AUTH_CONSTANTS.ROLE_ADMIN);
  });

  it('should validate session through AuthService', async () => {
    const signInResult = await service.signIn({
      email: AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL,
      password: 'password123',
      ip_address: '127.0.0.1',
      user_agent: 'VitestHexagonal/1.0',
    });

    const session = await service.validateSession(signInResult.token);
    expect(session.sub).toBe(AUTH_CONSTANTS.DEFAULT_ADMIN_ID);
  });

  it('should route request through AuthRestV1Router delegating to AuthService', async () => {
    const response = await router.route('GET', '/api/v1/auth/permissions');
    expect(response.statusCode).toBe(200);
    expect(response.payload.status).toBe('success');
  });

  it('should execute repository operations directly via AuthRepositoryPort', async () => {
    const user = await dbAdapter.findUserByEmail(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL);
    expect(user).not.toBeNull();
    expect(user?.email).toBe(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL);
  });
});
