import crypto from "crypto";
import { trace, SpanKind, SpanStatusCode } from "@opentelemetry/api";
import { RequestContextHolder } from '../tracing/request-context';
import { mapJson } from '../data-driven/json-map';
import type { JsonMapOp } from '../data-driven/transform.types';

export function getAuthHeaders(serviceSub = "web-app-service"): Record<string, string> {
  const secret = process.env.JWT_SECRET || "development-jwt-secret-key-32-bytes-min!!";
  const header = { alg: "HS256", typ: "JWT" };
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    sub: serviceSub,
    iat: now,
    exp: now + 3600,
  };

  const headerB64 = Buffer.from(JSON.stringify(header)).toString("base64url");
  const payloadB64 = Buffer.from(JSON.stringify(payload)).toString("base64url");
  const signingInput = `${headerB64}.${payloadB64}`;

  const signatureB64 = crypto
    .createHmac("sha256", secret)
    .update(signingInput)
    .digest("base64url");

  const traceId = crypto.randomBytes(16).toString("hex");
  const spanId = crypto.randomBytes(8).toString("hex");

  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${signingInput}.${signatureB64}`,
    "traceparent": `00-${traceId}-${spanId}-01`,
    "x-trace-id": traceId,
  };
}

export class HttpError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly retryAfter: string | null,
  ) {
    super(message);
    this.name = 'HttpError';
  }
}

async function request<T = unknown>(
  method: string,
  url: string,
  body?: unknown,
  headers?: Record<string, string>,
): Promise<{ data: T; status: number; headers: Headers }> {
  const tracer = trace.getTracer('http-client');

  return tracer.startActiveSpan(`HTTP ${method} ${url}`, { kind: SpanKind.CLIENT }, async (span) => {
    let contextHeaders: Record<string, string> = {};
    try {
      const ctx = RequestContextHolder.get();
      contextHeaders = {
        'x-request-id': ctx.requestId,
        'x-correlation-id': ctx.correlationId,
        'x-idempotency-key': ctx.idempotencyKey,
        'x-tenant-id': ctx.tenantId || 'tenant-default',
        traceparent: ctx.traceparent,
        tracestate: ctx.tracestate || 'rojo=1',
      };
    } catch {
      // Context holder optional
    }

    span.setAttribute('http.method', method);
    span.setAttribute('http.url', url);

    try {
      const res = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...contextHeaders,
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
      });

      span.setAttribute('http.status_code', res.status);

      if (!res.ok) {
        const error = new HttpError(
          `${method} ${url} failed with status ${res.status}`,
          res.status,
          res.headers.get('Retry-After'),
        );
        span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
        span.recordException(error);
        throw error;
      }

      const data = (await res.json()) as T;
      span.setStatus({ code: SpanStatusCode.OK });
      return { data, status: res.status, headers: res.headers };
    } catch (err: any) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: err?.message || 'HTTP Request Failed',
      });
      if (err instanceof Error) {
        span.recordException(err);
      }
      throw err;
    } finally {
      span.end();
    }
  });
}

export const httpClient = {
  get: <T = unknown>(url: string, headers?: Record<string, string>) =>
    request<T>('GET', url, undefined, headers),

  post: <T = unknown>(url: string, body: unknown, headers?: Record<string, string>) =>
    request<T>('POST', url, body, headers),

  patch: <T = unknown>(url: string, body: unknown, headers?: Record<string, string>) =>
    request<T>('PATCH', url, body, headers),

  put: <T = unknown>(url: string, body: unknown, headers?: Record<string, string>) =>
    request<T>('PUT', url, body, headers),

  delete: <T = unknown>(url: string, headers?: Record<string, string>) =>
    request<T>('DELETE', url, undefined, headers),
};

export async function executeQueryAdapter<T>(
  baseUrl: string,
  endpoint: string,
  params: Record<string, string | number | undefined>,
  serviceSub: string,
  transformOps?: JsonMapOp[]
): Promise<T> {
  const url = new URL(`${baseUrl}${endpoint}`);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null) {
      url.searchParams.set(k, String(v));
    }
  });

  const { data } = await httpClient.get<unknown>(
    url.toString(),
    getAuthHeaders(serviceSub)
  );

  return transformOps
    ? (mapJson(data as Record<string, unknown>, transformOps) as unknown as T)
    : (data as T);
}
