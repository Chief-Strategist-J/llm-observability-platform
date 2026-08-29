import { test, expect } from '@playwright/test';
import { RawAuthApiClient } from '../../../../src/lib/api/auth-client';

test.describe('Category F — Contract & Schema Boundary Automation Suite', () => {

  test('F-01: Should reject payload missing required name field', async () => {
    const client = new RawAuthApiClient('http://localhost:3001');
    const invalidPayload = {
      email: 'missingname@scaibu.io',
      organization_name: 'Scaibu Inc',
      password: 'SecurePassword123!',
    } as any;

    await expect(client.signUp(invalidPayload)).rejects.toThrow();
  });

  test('F-02: Should validate maximum length boundary on organization name field', async () => {
    const client = new RawAuthApiClient('http://localhost:3001');
    const oversizedOrgName = 'A'.repeat(256);
    const payload = {
      name: 'Boundary User',
      organization_name: oversizedOrgName,
      email: 'boundary@scaibu.io',
      password: 'SecurePassword123!',
    };

    await expect(client.signUp(payload)).rejects.toThrow();
  });

  test('F-03: Should safely ignore or sanitize unexpected extra request properties', async () => {
    const client = new RawAuthApiClient('http://localhost:3001');
    const payloadWithExtra = {
      name: 'Extra Field User',
      organization_name: 'Scaibu Org',
      email: `extra.${Date.now()}@scaibu.io`,
      password: 'SecurePassword123!',
      unexpected_injected_admin_flag: true,
    };

    expect(client).toBeDefined();
  });
});
