import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import {
  compose,
  withCorrelationId,
  withHttpTracing,
  withAuthGuard,
  isPublicRoute,
  type HttpMiddlewareCtx,
} from '@observability/shared-infra';

function extractSessionToken(req: NextRequest): string | undefined {
  const val =
    req.cookies.get('authjs.session-token')?.value ||
    req.cookies.get('__Secure-authjs.session-token')?.value ||
    req.cookies.get('next-auth.session-token')?.value;

  if (!val || val.trim() === '' || val === 'null' || val === 'undefined') {
    return undefined;
  }
  return val;
}

const pipeline = compose<HttpMiddlewareCtx, NextResponse>(
  withCorrelationId as any,
  withHttpTracing('web-app') as any,
  withAuthGuard('/auth/sign-in') as any,
)(async (ctx) => {
  if (ctx.redirectUrl) {
    const redirectRes = NextResponse.redirect(new URL(ctx.redirectUrl));
    Object.entries(ctx.customHeaders).forEach(([k, v]) => redirectRes.headers.set(k, v));
    return redirectRes;
  }

  const reqHeaders = new Headers();
  Object.entries(ctx.customHeaders).forEach(([k, v]) => reqHeaders.set(k, v));

  const res = NextResponse.next({ request: { headers: reqHeaders } });
  Object.entries(ctx.customHeaders).forEach(([k, v]) => res.headers.set(k, v));
  return res;
});

export function middleware(req: NextRequest): Promise<NextResponse> {
  const pathname = req.nextUrl.pathname;
  const headersRecord: Record<string, string | undefined> = {};
  req.headers.forEach((value, key) => {
    headersRecord[key.toLowerCase()] = value;
  });

  const ctx: HttpMiddlewareCtx = {
    reqUrl: req.url,
    pathname,
    method: req.method,
    headers: headersRecord,
    cookies: {},
    requestId: '',
    correlationId: '',
    traceparent: '',
    tracestate: '',
    tenantId: headersRecord['x-tenant-id'] || 'tenant-default',
    isPublic: isPublicRoute(pathname),
    sessionToken: extractSessionToken(req),
    customHeaders: {},
  };

  return pipeline(ctx) as Promise<NextResponse>;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
