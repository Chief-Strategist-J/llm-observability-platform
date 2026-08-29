import { test, expect } from '@playwright/test';
import { RawAuthApiClient } from '../../../src/lib/api/auth-client';

test.describe('Category J — Resource & Payload Limits Automation Suite', () => {

  test('J-01: Should handle payload size boundary constraints gracefully', async () => {
    const client = new RawAuthApiClient('http://localhost:3001');
    const oversizedName = 'B'.repeat(5000);
    await expect(client.signUp({
      name: oversizedName,
      organization_name: 'Limit Test Org',
      email: 'limit.test@scaibu.io',
      password: 'SecurePassword123!',
    })).rejects.toThrow();
  });
});
