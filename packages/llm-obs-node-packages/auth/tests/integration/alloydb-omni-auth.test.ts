import { describe, it, expect, beforeAll } from 'vitest';
import { AlloyDBOmniAuthAdapter } from '../../src/infra/adapters/postgres/alloydb-omni-auth.adapter';
import { AUTH_CONSTANTS } from '../../src/shared/constants/auth.constants';

describe('AlloyDB Omni Auth Repository (Integration Tests)', () => {
  let adapter: AlloyDBOmniAuthAdapter;

  beforeAll(async () => {
    adapter = new AlloyDBOmniAuthAdapter();
  });

  it('should find admin user record from AlloyDB Omni schema', async () => {
    const user = await adapter.findUserByEmail(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL);
    expect(user).not.toBeNull();
    expect(user?.email).toBe(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL);
    expect(user?.role).toBe(AUTH_CONSTANTS.DEFAULT_ADMIN_ROLE);
  });

  it('should list organizations for default admin user', async () => {
    const orgs = await adapter.listOrganizationsByUserId(AUTH_CONSTANTS.DEFAULT_ADMIN_ID);
    expect(orgs.length).toBeGreaterThan(0);
    expect(orgs[0]?.id).toBe(AUTH_CONSTANTS.DEFAULT_ORG_ID);
  });

  it('should manage token denylist for server-side sign-out', async () => {
    const fakeToken = 'test-token-123';
    expect(await adapter.isTokenDenylisted(fakeToken)).toBe(false);

    await adapter.addTokenToDenylist(fakeToken, Date.now() + 3600000);
    expect(await adapter.isTokenDenylisted(fakeToken)).toBe(true);
  });

  it('should save and find API key record in AlloyDB Omni table', async () => {
    const keyHash = 'hash-test-001';
    await adapter.saveApiKey({
      key_id: 'key-001',
      key_type: AUTH_CONSTANTS.KEY_TYPE_GENERAL,
      prefix: AUTH_CONSTANTS.API_KEY_PREFIX_GENERAL,
      permissions: [AUTH_CONSTANTS.PERMISSION_TRACES_READ],
      key_hash: keyHash,
      name: 'Integration Test Key',
      org_id: AUTH_CONSTANTS.DEFAULT_ORG_ID,
      created_at_ms: Date.now(),
      revoked: false,
    });

    const record = await adapter.findApiKeyByHash(keyHash);
    expect(record).not.toBeNull();
    expect(record?.name).toBe('Integration Test Key');
  });
});
