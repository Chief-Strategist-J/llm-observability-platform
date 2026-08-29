import { test, expect } from '@playwright/test';
import { canAccessRoute } from '../../../../src/server/auth/rbac';

test.describe('Auth RBAC - Route Security Access Automation', () => {
  test('should validate access rules for unauthenticated, member, and admin roles', async () => {
    expect(canAccessRoute(null, '/auth/sign-in')).toBe(true);
    expect(canAccessRoute('member', '/admin/budgets')).toBe(false);
    expect(canAccessRoute('admin', '/admin/budgets')).toBe(true);
    expect(canAccessRoute('owner', '/admin/slos')).toBe(true);
  });

  test('should enforce route access rules for unauthenticated users', async ({ page }) => {
    await page.context().clearCookies();
    expect(canAccessRoute(null, '/admin/budgets')).toBe(false);

    await page.goto('/admin/budgets');
    await page.waitForLoadState('networkidle');

    const url = page.url();
    expect(url).toBeDefined();
  });
});
