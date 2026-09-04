/**
 * @file types.ts
 * @description HTTP Middleware Pipeline Types & Context Contract.
 */

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
  next: HttpNext<Ctx, Result>
) => HttpNext<Ctx, Result>;
