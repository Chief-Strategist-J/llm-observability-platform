import { describe, it, expect } from 'vitest';
import { canAccessRoute } from '../../src/server/auth/rbac';

describe('RBAC Middleware Guard Unit Tests (TEST-FE2-01)', () => {
  it('blocks /admin/* routes for member role', () => {
    expect(canAccessRoute('member', '/admin/budgets')).toBe(false);
    expect(canAccessRoute('member', '/admin/slos')).toBe(false);
    expect(canAccessRoute('member', '/admin/compliance')).toBe(false);
  });

  it('allows /admin/* routes for admin and owner roles', () => {
    expect(canAccessRoute('admin', '/admin/budgets')).toBe(true);
    expect(canAccessRoute('owner', '/admin/slos')).toBe(true);
  });

  it('allows public routes without session/role', () => {
    expect(canAccessRoute(null, '/auth/sign-in')).toBe(true);
  });

  it('blocks non-public routes for unauthenticated users', () => {
    expect(canAccessRoute(null, '/costs')).toBe(false);
    expect(canAccessRoute(null, '/admin/budgets')).toBe(false);
  });

  it('allows general dashboard routes for member role', () => {
    expect(canAccessRoute('member', '/costs')).toBe(true);
    expect(canAccessRoute('member', '/latency')).toBe(true);
    expect(canAccessRoute('member', '/quality')).toBe(true);
    expect(canAccessRoute('member', '/settings/org')).toBe(true);
  });
});
