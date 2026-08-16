import { describe, it, expect } from 'vitest';
import { AuthService } from '../../service';
import { AlloyDBOmniAuthAdapter } from '../../../../infra/adapters/alloydb-omni-auth.adapter';
import { AUTH_CONSTANTS } from '../../../../shared/constants/auth.constants';

export async function runAuthServiceUnitTest(): Promise<boolean> {
  const repo = new AlloyDBOmniAuthAdapter();
  const service = new AuthService(repo);

  const result = await service.signIn({
    email: AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL,
    password: 'password123',
    ip_address: '127.0.0.1',
    user_agent: 'UnitTest/1.0',
  });

  if (!result.token || result.payload.email !== AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL) {
    throw new Error('signIn failed');
  }

  return true;
}

describe('AuthService Feature Unit Test', () => {
  it('should run auth service unit test successfully', async () => {
    const ok = await runAuthServiceUnitTest();
    expect(ok).toBe(true);
  });
});
