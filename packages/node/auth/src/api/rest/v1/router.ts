import { SpanStatusCode } from '@opentelemetry/api';
import type { AuthService } from '../../../features/auth/service';
import { handleVerifySession } from './handlers/session.handler';
import { withSpan } from '../../../infra/tracing/tracer';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';
import { createSuccessResponse, createErrorResponse, type StandardApiResponse } from '../../../shared/errors/error-handler';
import { ROUTE_RULES, type RouteContext, type RouteRule } from './route.rules';

function compilePathPattern(pattern: string): { regex: RegExp; paramNames: string[] } {
  const paramNames: string[] = [];
  const regexStr = pattern.replace(/:([a-zA-Z0-9_]+)/g, (_, name) => {
    paramNames.push(name);
    return '([^/]+)';
  });
  return { regex: new RegExp(`^${regexStr}$`), paramNames };
}

interface CompiledRouteRule extends RouteRule {
  regex: RegExp;
  paramNames: string[];
}

export class AuthRestV1Router {
  private readonly compiledRules: CompiledRouteRule[];

  constructor(private readonly service: AuthService) {
    this.compiledRules = ROUTE_RULES.map((rule) => {
      const { regex, paramNames } = compilePathPattern(rule.pattern);
      return { ...rule, regex, paramNames };
    });
  }

  private findMatchingRule(method: string, path: string): { rule: CompiledRouteRule; params: Record<string, string> } | null {
    for (const rule of this.compiledRules) {
      if (rule.method !== method) continue;
      const match = rule.regex.exec(path);
      if (match) {
        const params: Record<string, string> = {};
        rule.paramNames.forEach((name, index) => {
          params[name] = decodeURIComponent(match[index + 1]!);
        });
        return { rule, params };
      }
    }
    return null;
  }

  async route(method: string, path: string, body?: unknown, headers?: Record<string, string>, queryParams?: Record<string, string>): Promise<{ statusCode: number; payload: StandardApiResponse<unknown> }> {
    return withSpan(`REST ${method} ${path}`, async (span) => {
      span.setAttribute('http.method', method);
      span.setAttribute('http.target', path);

      if (headers) {
        if (headers['x-request-id']) span.setAttribute('x-request-id', headers['x-request-id']);
        if (headers['x-correlation-id']) span.setAttribute('x-correlation-id', headers['x-correlation-id']);
        if (headers['x-tenant-id']) span.setAttribute('x-tenant-id', headers['x-tenant-id']);
      }

      if (body && typeof body === 'object') {
        const b = body as Record<string, unknown>;
        if (typeof b['email'] === 'string') span.setAttribute('user.email', b['email']);
        if (typeof b['org_id'] === 'string') span.setAttribute('org.id', b['org_id']);
        if (typeof b['organization_name'] === 'string') span.setAttribute('org.name', b['organization_name']);
      }

      try {
        const matched = this.findMatchingRule(method, path);
        if (!matched) {
          throw new Error(`Route not found: ${method} ${path}`);
        }

        const { rule, params } = matched;
        span.setAttribute('route.name', rule.name);

        const authHeader = headers?.[AUTH_CONSTANTS.HEADERS.AUTHORIZATION] ?? headers?.[AUTH_CONSTANTS.HEADERS.AUTHORIZATION_CAMEL];
        let session: any = undefined;

        if (rule.requiresAuth) {
          session = await handleVerifySession(this.service, authHeader);
          if (session?.payload?.sub) span.setAttribute('user.id', session.payload.sub);
          if (session?.payload?.org?.org_id) span.setAttribute('org.id', session.payload.org.org_id);
        }

        const ctx: RouteContext = {
          service: this.service,
          body,
          headers,
          queryParams,
          authHeader,
          params,
        };

        const resultData = await rule.handler(ctx, session);
        const statusCode = rule.successStatus ?? 200;

        span.setAttribute('http.status_code', statusCode);
        return {
          statusCode,
          payload: createSuccessResponse(resultData, rule.successMessage),
        };
      } catch (err: unknown) {
        const errorRes = createErrorResponse(err);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: errorRes.payload.message,
        });
        if (err instanceof Error) {
          span.recordException(err);
        } else {
          span.recordException(new Error(errorRes.payload.message));
        }
        span.setAttribute('error', true);
        span.setAttribute('error.code', errorRes.payload.error?.code ?? 'UNKNOWN_ERROR');
        span.setAttribute('error.message', errorRes.payload.message);
        span.setAttribute('http.status_code', errorRes.statusCode);
        return errorRes;
      }
    });
  }
}
