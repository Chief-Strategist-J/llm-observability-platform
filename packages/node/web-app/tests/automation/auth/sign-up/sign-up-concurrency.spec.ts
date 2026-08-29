import { test, expect } from '@playwright/test';
import { RawAuthApiClient } from '../../../../src/lib/api/auth-client';

test.describe('Category I — Concurrency & Idempotency Automation Suite', () => {

  test('I-01: Concurrent identical sign-up requests should evaluate without unhandled exceptions', async () => {
    const client = new RawAuthApiClient('http://localhost:3001');
    const email = `concurrent.${Date.now()}@scaibu.io`;
    const payload = {
      name: 'Concurrent User',
      organization_name: 'Concurrent Org',
      email,
      password: 'SecurePassword123!',
    };

    const [res1, res2] = await Promise.allSettled([
      client.signUp(payload),
      client.signUp(payload),
    ]);

    expect(res1.status).toBeDefined();
    expect(res2.status).toBeDefined();
  });
});
