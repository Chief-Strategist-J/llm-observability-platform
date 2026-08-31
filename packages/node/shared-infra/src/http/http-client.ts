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

// In-Memory Cache for Centralized Caching
const httpCache = new Map<string, { data: unknown; exp: number }>();

// Circuit Breaker State Tracking
interface CircuitState {
  failures: number;
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  nextAttempt: number;
}
const circuitStates = new Map<string, CircuitState>();

async function request<T = unknown>(
  method: string,
  url: string,
  body?: unknown,
  headers?: Record<string, string>,
  options: { retries?: number; ttlMs?: number; failureThreshold?: number } = {}
): Promise<{ data: T; status: number; headers: Headers }> {
  const maxRetries = options.retries ?? 3;
  const ttlMs = options.ttlMs ?? 5000;
  const failureThreshold = options.failureThreshold ?? 5;

  const cacheKey = `${method}:${url}:${body ? JSON.stringify(body) : ''}`;
  const tracer = trace.getTracer('http-client');

  return tracer.startActiveSpan(`HTTP ${method} ${url}`, { kind: SpanKind.CLIENT }, async (span) => {
    // Check Cache
    const cached = httpCache.get(cacheKey);
    if (cached && Date.now() < cached.exp) {
      span.setAttribute('http.cache_hit', true);
      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
      return { data: cached.data as T, status: 200, headers: new Headers() };
    }
    span.setAttribute('http.cache_hit', false);

    // Check Circuit Breaker
    let circuit = circuitStates.get(url);
    if (!circuit) {
      circuit = { failures: 0, state: 'CLOSED', nextAttempt: 0 };
      circuitStates.set(url, circuit);
    }

    if (circuit.state === 'OPEN') {
      if (Date.now() > circuit.nextAttempt) {
        circuit.state = 'HALF_OPEN';
      } else {
        const cbErr = new Error(`CircuitBreaker: Request to ${url} blocked due to active OPEN state.`);
        span.setStatus({ code: SpanStatusCode.ERROR, message: cbErr.message });
        span.recordException(cbErr);
        span.end();
        throw cbErr;
      }
    }

    span.setAttribute('http.circuit_state', circuit.state);

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
      span.setAttribute('tenant.id', ctx.tenantId || 'tenant-default');
    } catch {
      // Optional context
    }

    span.setAttribute('http.method', method);
    span.setAttribute('http.url', url);

    let attempt = 0;
    let lastError: unknown;

    while (attempt <= maxRetries) {
      try {
        span.setAttribute('http.retry_attempt', attempt);
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
          throw new HttpError(
            `${method} ${url} failed with status ${res.status}`,
            res.status,
            res.headers.get('Retry-After'),
          );
        }

        const data = (await res.json()) as T;

        // Reset Circuit Breaker on Success
        circuit.failures = 0;
        circuit.state = 'CLOSED';

        // Cache Response
        httpCache.set(cacheKey, { data, exp: Date.now() + ttlMs });

        span.setStatus({ code: SpanStatusCode.OK });
        return { data, status: res.status, headers: res.headers };
      } catch (err: any) {
        lastError = err;
        attempt++;

        // Update Circuit Breaker
        circuit.failures++;
        if (circuit.failures >= failureThreshold) {
          circuit.state = 'OPEN';
          circuit.nextAttempt = Date.now() + 10000;
        }

        if (attempt <= maxRetries && err?.status !== 401 && err?.status !== 403) {
          const backoff = 200 * Math.pow(2, attempt - 1);
          await new Promise((res) => setTimeout(res, backoff));
        } else {
          break;
        }
      }
    }

    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: lastError instanceof Error ? lastError.message : 'HTTP Request Retry Pipeline Failed',
    });
    if (lastError instanceof Error) {
      span.recordException(lastError);
    }
    span.end();
    throw lastError;
  });
}

export const httpClient = {
  get: <T = unknown>(url: string, headers?: Record<string, string>, options?: { retries?: number; ttlMs?: number }) =>
    request<T>('GET', url, undefined, headers, options),

  post: <T = unknown>(url: string, body: unknown, headers?: Record<string, string>, options?: { retries?: number; ttlMs?: number }) =>
    request<T>('POST', url, body, headers, options),

  patch: <T = unknown>(url: string, body: unknown, headers?: Record<string, string>, options?: { retries?: number; ttlMs?: number }) =>
    request<T>('PATCH', url, body, headers, options),

  put: <T = unknown>(url: string, body: unknown, headers?: Record<string, string>, options?: { retries?: number; ttlMs?: number }) =>
    request<T>('PUT', url, body, headers, options),

  delete: <T = unknown>(url: string, headers?: Record<string, string>, options?: { retries?: number; ttlMs?: number }) =>
    request<T>('DELETE', url, undefined, headers, options),
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
