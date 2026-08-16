import { AuthService } from '../../src/features/auth/service';
import { AlloyDBOmniAuthAdapter } from '../../src/infra/adapters/alloydb-omni-auth.adapter';
import { AUTH_CONSTANTS } from '../../src/shared/constants/auth.constants';

describe('AuthService (Unit Tests)', () => {
  let authService: AuthService;

  beforeEach(() => {
    const repository = new AlloyDBOmniAuthAdapter();
    authService = new AuthService(repository);
  });

  it('should sign up a new user with unique organization and role', async () => {
    const result = await authService.signUp({
      email: 'newuser@observability.io',
      password: 'StrongPass123!',
      name: 'New User',
      organization_name: 'Unique Corp',
      role: AUTH_CONSTANTS.ROLE_ADMIN,
    });

    expect(result.token).toBeDefined();
    expect(result.user.email).toBe('newuser@observability.io');
    expect(result.user.org_name).toBe('Unique Corp');
    expect(result.user.role).toBe(AUTH_CONSTANTS.ROLE_ADMIN);
  });

  it('should generate 3-tier API keys with permission binding', async () => {
    const genResult = await authService.generateApiKey({
      org_id: AUTH_CONSTANTS.DEFAULT_ORG_ID,
      name: 'General Key',
      key_type: AUTH_CONSTANTS.KEY_TYPE_GENERAL,
      permissions: [AUTH_CONSTANTS.PERMISSION_TRACES_READ],
    });

    expect(genResult.rawKey.startsWith(AUTH_CONSTANTS.API_KEY_PREFIX_GENERAL)).toBe(true);

    const verifyGen = await authService.verifyApiKey({
      key: genResult.rawKey,
      required_permission: AUTH_CONSTANTS.PERMISSION_TRACES_READ,
    });

    expect(verifyGen.valid).toBe(true);
    expect(verifyGen.authorized).toBe(true);

    const secResult = await authService.generateApiKey({
      org_id: AUTH_CONSTANTS.DEFAULT_ORG_ID,
      name: 'Super Secret Key',
      key_type: AUTH_CONSTANTS.KEY_TYPE_SUPER_SECRET,
      permissions: [AUTH_CONSTANTS.PERMISSION_ADMIN_ALL],
    });

    expect(secResult.rawKey.startsWith(AUTH_CONSTANTS.API_KEY_PREFIX_SUPER_SECRET)).toBe(true);
  });
});
