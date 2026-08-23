import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { withSpan } from '@observability/core/tracing';
import { SpanKind } from '@opentelemetry/api';

const PUBLIC_ROUTES = [
  '/auth/sign-in',
  '/auth/sign-up',
  '/auth/callback',
];

function isPublicPath(pathname: string): boolean {
  if (pathname.startsWith('/_next') || pathname.startsWith('/api') || pathname.includes('.') || pathname === '/favicon.ico') {
    return true;
  }
  return PUBLIC_ROUTES.some((route) => pathname.startsWith(route));
}

function getSessionToken(req: NextRequest): string | undefined {
  return (
    req.cookies.get('authjs.session-token')?.value ||
    req.cookies.get('__Secure-authjs.session-token')?.value ||
    req.cookies.get('next-auth.session-token')?.value
  );
}

function generateW3CTraceparent(): string {
  const hexChars = '0123456789abcdef';
  let traceId = '';
  let spanId = '';
  for (let i = 0; i < 32; i++) traceId += hexChars[Math.floor(Math.random() * 16)];
  for (let i = 0; i < 16; i++) spanId += hexChars[Math.floor(Math.random() * 16)];
  return `00-${traceId}-${spanId}-01`;
}

export function middleware(req: NextRequest) {
  const pathname = req.nextUrl.pathname;
  const method = req.method;

  const requestId = req.headers.get('x-request-id') || `req-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
  const correlationId = req.headers.get('x-correlation-id') || requestId;
  const traceparent = req.headers.get('traceparent') || generateW3CTraceparent();

  const requestHeaders = new Headers(req.headers);
  requestHeaders.set('x-request-id', requestId);
  requestHeaders.set('x-correlation-id', correlationId);
  requestHeaders.set('traceparent', traceparent);
  requestHeaders.set('tracestate', req.headers.get('tracestate') || 'rojo=1');

  withSpan(
    `HTTP ${method} ${pathname}`,
    async (span) => {
      span.setAttribute('http.method', method);
      span.setAttribute('http.target', pathname);
      span.setAttribute('x-request-id', requestId);
      span.setAttribute('request_id', requestId);
      span.setAttribute('x-correlation-id', correlationId);
      span.setAttribute('correlation_id', correlationId);
    },
    { kind: SpanKind.SERVER, serviceName: 'web-app' }
  ).catch(() => {});

  if (!isPublicPath(pathname)) {
    const sessionToken = getSessionToken(req);
    if (!sessionToken) {
      const signInUrl = new URL('/auth/sign-in', req.url);
      signInUrl.searchParams.set('callbackUrl', pathname);
      const redirectRes = NextResponse.redirect(signInUrl);
      redirectRes.headers.set('x-request-id', requestId);
      redirectRes.headers.set('x-correlation-id', correlationId);
      redirectRes.headers.set('traceparent', traceparent);
      return redirectRes;
    }
  }

  const res = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });

  res.headers.set('x-request-id', requestId);
  res.headers.set('x-correlation-id', correlationId);
  res.headers.set('traceparent', traceparent);
  res.headers.set('tracestate', 'rojo=1');

  return res;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
