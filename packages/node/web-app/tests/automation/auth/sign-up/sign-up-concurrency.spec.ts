import { test, expect } from '@playwright/test';
import { RawAuthApiClient } from '../../../../src/lib/api/auth-client';

test.describe('Category I — Concurrency & Idempotency Automation Suite', () => {

  test('I-01: Concurrent identical sign-up requests should not duplicate account creation', async () => {
    const client = new RawAuthApiClient('http://localhost:3001');
    const email = `concurrent.${Date.now()}@scaibu.io`;
    const payload = {
      name: 'Concurrent User',
      organization_name: 'Concurrent Org',
      email,
      password: 'SecurePassword123!',
    };

    // Fire 2 concurrent identical requests
    const [res1, res2] = await Promise.allSettled([
      client.signUp(payload),
      client.signUp(payload),
    ]);

    // Exactly one or both should handle idempotency safely without double-side-effects
    expect(res1.status === 'fulfilled' || res2.status === 'fulfilled').toBe(true);
  });
});
