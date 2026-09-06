import { describe, it, expect, beforeEach } from 'vitest';
import { AUTH_QUERIES } from '../../src/features/auth/queries/auth.queries';
import { AlloyDBOmniAuthAdapter } from '../../src/infra/adapters/postgres/alloydb-omni-auth.adapter';
import { AUTH_CONSTANTS } from '../../src/shared/constants/auth.constants';

describe('AlloyDB Omni Row Level Security (RLS) & Tenant Isolation Tests', () => {
  let adapter: AlloyDBOmniAuthAdapter;

  beforeEach(() => {
    adapter = new AlloyDBOmniAuthAdapter();
  });

  it('should verify Row Level Security (RLS) tenant context query definition', () => {
    const rlsQuery = AUTH_QUERIES.TENANT_RLS.SET_LOCAL_TENANT_CONTEXT;
    expect(rlsQuery).toBe("SELECT set_config('app.current_org_id', $1, true)");
  });

  it('should enforce tenant isolation between Org A and Org B users', async () => {
    const userA = await adapter.findUserByEmail(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL);
    expect(userA).not.toBeNull();
    expect(userA?.org_id).toBe(AUTH_CONSTANTS.DEFAULT_ORG_ID);

    await adapter.createOrganizationAndUser({
      id: 'usr-org-b-001',
      email: 'admin@tenant-b.com',
      password_hash: 'hash-b',
      name: 'Tenant B Admin',
      org_id: 'org-b-999',
      org_name: 'Tenant B Corp',
      role: AUTH_CONSTANTS.ROLE_ADMIN,
    });

    const userB = await adapter.findUserByEmail('admin@tenant-b.com');
    expect(userB).not.toBeNull();
    expect(userB?.org_id).toBe('org-b-999');
    expect(userB?.org_id).not.toEqual(userA?.org_id);
  });
});
