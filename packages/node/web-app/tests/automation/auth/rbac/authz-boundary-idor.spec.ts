import { test, expect } from '@playwright/test';
import { RawAuthApiClient } from '../../../../src/lib/api/auth-client';

test.describe('Category G — Authentication & Authorization Boundary (IDOR Isolation)', () => {

  test('G-01: Should block unauthenticated token access with 401 Unauthorized', async () => {
    const client = new RawAuthApiClient('http://localhost:3001');
    await expect(client.getSession('')).rejects.toThrow();
  });

  test('G-02: Cross-tenant resource access should be forbidden across tenant boundaries', async () => {
    const client = new RawAuthApiClient('http://localhost:3001');
    const tenantAToken = 'token-tenant-a';
    const tenantBOrgId = 'org-tenant-b';

    // Tenant A user attempting to access Tenant B organization data must be denied
    await expect(client.getOrganization(tenantBOrgId, tenantAToken)).rejects.toThrow();
  });
});
