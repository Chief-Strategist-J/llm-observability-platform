import { AuthService } from '../../src/features/auth/service';
import { AlloyDBOmniAuthAdapter } from '../../src/infra/adapters/alloydb-omni-auth.adapter';
import { RedisSessionAdapter } from '../../src/infra/adapters/redis-session.adapter';
import { AUTH_CONSTANTS } from '../../src/shared/constants/auth.constants';

describe('AuthService (Unit Tests)', () => {
  let authService: AuthService;

  beforeEach(() => {
    const repository = new AlloyDBOmniAuthAdapter();
    const sessionAdapter = new RedisSessionAdapter();
    authService = new AuthService(repository, sessionAdapter, 'test-secret-key');
  });

  it('should authenticate admin user with valid credentials', async () => {
    const session = await authService.signIn({
      email: AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL,
      password: 'password123',
    });

    expect(session).toBeDefined();
    expect(session.payload.email).toBe(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL);
    expect(session.payload.org.role).toBe(AUTH_CONSTANTS.DEFAULT_ADMIN_ROLE);
    expect(session.token).toBeDefined();
  });

  it('should reject invalid password', async () => {
    await expect(
      authService.signIn({
        email: AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL,
        password: 'wrong-password',
      })
    ).rejects.toThrow();
  });
});
