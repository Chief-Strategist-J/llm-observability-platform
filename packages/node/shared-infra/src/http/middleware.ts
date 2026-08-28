import { SpanKind } from '@opentelemetry/api';
import { RequestContextHolder } from '../tracing/request-context';
import { withSpan } from '../tracing/tracer';

export interface HttpMiddlewareCtx {
  reqUrl: string;
  pathname: string;
  method: string;
  headers: Record<string, string | undefined>;
  cookies: Record<string, string | undefined>;
  requestId: string;
  correlationId: string;
  traceparent: string;
  tracestate: string;
  tenantId: string;
  isPublic: boolean;
  sessionToken?: string;
  redirectUrl?: string;
  customHeaders: Record<string, string>;
}

export type HttpNext<Ctx = HttpMiddlewareCtx, Result = unknown> = (ctx: Ctx) => Promise<Result>;
export type HttpMiddleware<Ctx = HttpMiddlewareCtx, Result = unknown> = (
  next: HttpNext<Ctx, Result>,
) => HttpNext<Ctx, Result>;

export function compose<Ctx, Result>(...middlewares: HttpMiddleware<Ctx, Result>[]): HttpMiddleware<Ctx, Result> {
  return (finalNext: HttpNext<Ctx, Result>) => middlewares.reduceRight((next, mw) => mw(next), finalNext);
}

const PUBLIC_ROUTES = ['/auth/sign-in', '/auth/sign-up', '/auth/callback'];

export function isPublicRoute(pathname: string, publicRoutes: string[] = PUBLIC_ROUTES): boolean {
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.') ||
    pathname === '/favicon.ico'
  ) {
    return true;
  }
  return publicRoutes.some((route) => pathname.startsWith(route));
}

export const withCorrelationId: HttpMiddleware<HttpMiddlewareCtx, unknown> = (next) => async (ctx) => {
  const requestId =
    ctx.headers['x-request-id'] ||
    `req-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
  const correlationId = ctx.headers['x-correlation-id'] || requestId;
  const traceparent = ctx.headers['traceparent'] || RequestContextHolder.generateW3CTraceparent();
  const tracestate = ctx.headers['tracestate'] || 'rojo=1';

  const updatedCtx: HttpMiddlewareCtx = {
    ...ctx,
    requestId,
    correlationId,
    traceparent,
    tracestate,
    customHeaders: {
      ...ctx.customHeaders,
      'x-request-id': requestId,
      'x-correlation-id': correlationId,
      traceparent,
      tracestate,
    },
  };

  return next(updatedCtx);
};

export const withHttpTracing = (serviceName = 'http-service'): HttpMiddleware<HttpMiddlewareCtx, unknown> => {
  return (next) => async (ctx) => {
    withSpan(
      `HTTP ${ctx.method} ${ctx.pathname}`,
      async (span) => {
        span.setAttribute('http.method', ctx.method);
        span.setAttribute('http.target', ctx.pathname);
        span.setAttribute('x-request-id', ctx.requestId);
        span.setAttribute('request_id', ctx.requestId);
        span.setAttribute('x-correlation-id', ctx.correlationId);
        span.setAttribute('correlation_id', ctx.correlationId);
      },
      { kind: SpanKind.SERVER, serviceName },
    ).catch(() => {});

    return next(ctx);
  };
};

export const withAuthGuard = (signInRoute = '/auth/sign-in'): HttpMiddleware<HttpMiddlewareCtx, unknown> => {
  return (next) => async (ctx) => {
    if (!ctx.isPublic && !ctx.sessionToken) {
      const redirect = new URL(signInRoute, ctx.reqUrl);
      redirect.searchParams.set('callbackUrl', ctx.pathname);

      return next({
        ...ctx,
        redirectUrl: redirect.toString(),
      });
    }
    return next(ctx);
  };
};
