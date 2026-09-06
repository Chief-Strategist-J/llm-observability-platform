import type { OrgRole } from '@observability/api-types';

export const ADMIN_ROUTES = [
  '/admin/budgets',
  '/admin/slos',
  '/admin/templates',
  '/admin/compliance',
  '/admin/feature-flags',
];

export const PUBLIC_ROUTES = [
  '/auth/sign-in',
  '/auth/callback',
];

export function canAccessRoute(role: OrgRole | null | undefined, pathname: string): boolean {
  if (PUBLIC_ROUTES.some((route) => pathname.startsWith(route))) {
    return true;
  }

  if (!role) {
    return false;
  }

  const isAdminRoute = ADMIN_ROUTES.some((route) => pathname.startsWith(route)) || pathname.startsWith('/admin');

  if (isAdminRoute) {
    return role === 'owner' || role === 'admin';
  }

  return true;
}
