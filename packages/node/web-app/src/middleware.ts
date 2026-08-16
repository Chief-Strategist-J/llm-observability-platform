import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { canAccessRoute } from './server/auth/rbac';
import type { OrgRole } from '@observability/api-types';

function isPublicPath(pathname: string): boolean {
  return (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api/auth') ||
    pathname.includes('.') ||
    pathname === '/favicon.ico'
  );
}

function getSessionToken(req: NextRequest): string | undefined {
  return (
    req.cookies.get('authjs.session-token')?.value ||
    req.cookies.get('__Secure-authjs.session-token')?.value ||
    req.cookies.get('next-auth.session-token')?.value
  );
}

function getUnauthorizedRedirect(req: NextRequest, pathname: string, sessionCookie?: string) {
  if (!sessionCookie) {
    const signInUrl = new URL('/auth/sign-in', req.url);
    signInUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(signInUrl);
  }
  return NextResponse.redirect(new URL('/', req.url));
}

export function middleware(req: NextRequest) {
  const pathname = req.nextUrl.pathname;

  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  const sessionCookie = getSessionToken(req);
  const mockRole: OrgRole = (req.cookies.get('mock_role')?.value as OrgRole) || 'owner';
  const isAllowed = canAccessRoute(sessionCookie ? mockRole : null, pathname);

  if (!isAllowed) {
    return getUnauthorizedRedirect(req, pathname, sessionCookie);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
