import crypto from "crypto";
import { trace, SpanKind, SpanStatusCode } from "@opentelemetry/api";
import { RequestContextHolder } from '../tracing/request-context';
import { mapJson } from '../data-driven/json-map';
import type { JsonMapOp } from '../data-driven/transform.types';
import { HTTP_CONSTANTS } from './constants';

export * from './constants';

// --- 1. Resilient Strategy Definitions & Contracts ---

export function calculateFullJitterBackoff(attempt: number, baseMs = 200, maxMs = 10000): number {
  const cap = Math.min(maxMs, baseMs * Math.pow(2, attempt - 1));
  return Math.floor(Math.random() * cap);
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

export interface RequestConfig {
  method: string;
  url: string;
  body?: unknown;
  headers?: Record<string, string>;
  serviceSub?: string;
  retries?: number;
  ttlMs?: number;
  failureThreshold?: number;
}

export type HeaderProviderFn = (config: RequestConfig) => Record<string, string> | Promise<Record<string, string>>;
export type RequestInterceptorFn = (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
export type ResponseInterceptorFn<T = unknown> = (data: T, response: Response, config: RequestConfig) => T | Promise<T>;
export type ErrorInterceptorFn = (error: unknown, config: RequestConfig) => unknown;

export interface ICacheStore {
  get<T>(key: string): T | undefined;
  set<T>(key: string, data: T, ttlMs: number): void;
  clear(): void;
}

export interface ICircuitBreakerState {
  failures: number;
  state: typeof HTTP_CONSTANTS.CIRCUIT_CLOSED | typeof HTTP_CONSTANTS.CIRCUIT_OPEN | typeof HTTP_CONSTANTS.CIRCUIT_HALF_OPEN;
  nextAttempt: number;
}

// --- 2. Centralized Cache & Circuit Breaker Implementations ---

export class InMemoryCacheStore implements ICacheStore {
  private readonly store = new Map<string, { data: unknown; exp: number }>();

  get<T>(key: string): T | undefined {
    const entry = this.store.get(key);
    if (entry && Date.now() < entry.exp) {
      return entry.data as T;
    }
    return undefined;
  }

  set<T>(key: string, data: T, ttlMs: number): void {
    this.store.set(key, { data, exp: Date.now() + ttlMs });
  }

  clear(): void {
    this.store.clear();
  }
}

export class StandardCircuitBreaker {
  private readonly states = new Map<string, ICircuitBreakerState>();

  public getState(url: string): ICircuitBreakerState {
    let state = this.states.get(url);
    if (!state) {
      state = { failures: 0, state: HTTP_CONSTANTS.CIRCUIT_CLOSED, nextAttempt: 0 };
      this.states.set(url, state);
    }
    return state;
  }

  public canExecute(url: string): boolean {
    const state = this.getState(url);
    if (state.state === HTTP_CONSTANTS.CIRCUIT_OPEN) {
      if (Date.now() > state.nextAttempt) {
        state.state = HTTP_CONSTANTS.CIRCUIT_HALF_OPEN;
        return true;
      }
      return false;
    }
    return true;
  }

  public onSuccess(url: string): void {
    const state = this.getState(url);
    state.failures = 0;
    state.state = HTTP_CONSTANTS.CIRCUIT_CLOSED;
  }

  public onFailure(url: string, threshold = 5, cooldownMs = 10000): void {
    const state = this.getState(url);
    state.failures++;
    if (state.failures >= threshold) {
      state.state = HTTP_CONSTANTS.CIRCUIT_OPEN;
      state.nextAttempt = Date.now() + cooldownMs;
    }
  }
}

// --- 3. Pluggable Scalable HttpClient Engine ---

export class ScalableHttpClient {
  private readonly headerProviders: HeaderProviderFn[] = [];
  private readonly requestInterceptors: RequestInterceptorFn[] = [];
  private readonly responseInterceptors: ResponseInterceptorFn[] = [];
  private readonly errorInterceptors: ErrorInterceptorFn[] = [];
  private cacheStore: ICacheStore = new InMemoryCacheStore();
  private circuitBreaker = new StandardCircuitBreaker();

  constructor() {
    this.registerDefaultHeaderProviders();
  }

  // --- Pluggable Registries ---
  public registerHeaderProvider(provider: HeaderProviderFn): void {
    this.headerProviders.push(provider);
  }

  public registerRequestInterceptor(interceptor: RequestInterceptorFn): void {
    this.requestInterceptors.push(interceptor);
  }

  public registerResponseInterceptor(interceptor: ResponseInterceptorFn): void {
    this.responseInterceptors.push(interceptor);
  }

  public registerErrorInterceptor(interceptor: ErrorInterceptorFn): void {
    this.errorInterceptors.push(interceptor);
  }

  public setCacheStore(cache: ICacheStore): void {
    this.cacheStore = cache;
  }

  public setCircuitBreaker(cb: StandardCircuitBreaker): void {
    this.circuitBreaker = cb;
  }

  // --- Default Builtin Header Providers ---
  private registerDefaultHeaderProviders(): void {
    // 1. Auth JWT Provider
    this.registerHeaderProvider((config) => {
      const sub = config.serviceSub || HTTP_CONSTANTS.DEFAULT_SERVICE_SUB;
      return getAuthHeaders(sub);
    });

    // 2. W3C & Context Provider
    this.registerHeaderProvider(() => {
      try {
        const ctx = RequestContextHolder.get();
        return {
          [HTTP_CONSTANTS.HEADER_X_REQUEST_ID]: ctx.requestId,
          [HTTP_CONSTANTS.HEADER_X_CORRELATION_ID]: ctx.correlationId,
          [HTTP_CONSTANTS.HEADER_X_IDEMPOTENCY_KEY]: ctx.idempotencyKey,
          [HTTP_CONSTANTS.HEADER_X_TENANT_ID]: ctx.tenantId || HTTP_CONSTANTS.DEFAULT_TENANT_ID,
          [HTTP_CONSTANTS.HEADER_TRACEPARENT]: ctx.traceparent,
          [HTTP_CONSTANTS.HEADER_TRACESTATE]: ctx.tracestate || HTTP_CONSTANTS.DEFAULT_TRACESTATE,
        };
      } catch {
        return {};
      }
    });
  }

  // --- Core Request Pipeline Execution ---
  public async execute<T>(rawConfig: RequestConfig): Promise<{ data: T; status: number; headers: Headers }> {
    let config = { ...rawConfig };
    for (const reqInterceptor of this.requestInterceptors) {
      config = await reqInterceptor(config);
    }

    const maxRetries = config.retries ?? 3;
    const ttlMs = config.ttlMs ?? 5000;
    const failureThreshold = config.failureThreshold ?? 5;
    const cacheKey = `${config.method}:${config.url}:${config.body ? JSON.stringify(config.body) : ''}`;
    const tracer = trace.getTracer('http-client');

    return tracer.startActiveSpan(`HTTP ${config.method} ${config.url}`, { kind: SpanKind.CLIENT }, async (span) => {
      // 1. Cache Lookup
      const cachedData = this.cacheStore.get<T>(cacheKey);
      if (cachedData !== undefined) {
        span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_CACHE_HIT, true);
        span.setStatus({ code: SpanStatusCode.OK });
        span.end();
        return { data: cachedData, status: 200, headers: new Headers() };
      }
      span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_CACHE_HIT, false);

      // 2. Circuit Breaker Check
      if (!this.circuitBreaker.canExecute(config.url)) {
        const cbErr = new Error(`CircuitBreaker: Request to ${config.url} blocked due to active OPEN state.`);
        span.setStatus({ code: SpanStatusCode.ERROR, message: cbErr.message });
        span.recordException(cbErr);
        span.end();
        throw cbErr;
      }
      const circuitState = this.circuitBreaker.getState(config.url);
      span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_CIRCUIT_STATE, circuitState.state);

      // 3. Resolve Header Providers
      let resolvedHeaders: Record<string, string> = {
        [HTTP_CONSTANTS.HEADER_CONTENT_TYPE]: HTTP_CONSTANTS.CONTENT_TYPE_JSON,
        ...config.headers,
      };

      for (const provider of this.headerProviders) {
        const providerHeaders = await provider(config);
        resolvedHeaders = { ...resolvedHeaders, ...providerHeaders };
      }

      span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_METHOD, config.method);
      span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_URL, config.url);
      if (resolvedHeaders[HTTP_CONSTANTS.HEADER_X_TENANT_ID]) {
        span.setAttribute(HTTP_CONSTANTS.ATTR_TENANT_ID, resolvedHeaders[HTTP_CONSTANTS.HEADER_X_TENANT_ID]!);
      }

      let attempt = 0;
      let lastError: unknown;

      while (attempt <= maxRetries) {
        try {
          span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_RETRY_ATTEMPT, attempt);
          const res = await fetch(config.url, {
            method: config.method,
            headers: resolvedHeaders,
            body: config.body ? JSON.stringify(config.body) : undefined,
          });

          span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_STATUS_CODE, res.status);

          if (!res.ok) {
            throw new HttpError(
              `${config.method} ${config.url} failed with status ${res.status}`,
              res.status,
              res.headers.get(HTTP_CONSTANTS.HEADER_RETRY_AFTER),
            );
          }

          let data = (await res.json()) as T;

          // Run Response Interceptors
          for (const resInterceptor of this.responseInterceptors) {
            data = (await resInterceptor(data, res, config)) as T;
          }

          // Reset Circuit Breaker & Cache
          this.circuitBreaker.onSuccess(config.url);
          this.cacheStore.set(cacheKey, data, ttlMs);

          span.setStatus({ code: SpanStatusCode.OK });
          return { data, status: res.status, headers: res.headers };
        } catch (err: any) {
          lastError = err;
          attempt++;

          this.circuitBreaker.onFailure(config.url, failureThreshold);

          // Run Error Interceptors
          for (const errInterceptor of this.errorInterceptors) {
            errInterceptor(err, config);
          }

          if (attempt <= maxRetries && err?.status !== 401 && err?.status !== 403) {
            const backoff = calculateFullJitterBackoff(attempt, 200, 10000);
            span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_RETRY_BACKOFF_MS, backoff);
            await new Promise((r) => setTimeout(r, backoff));
          } else {
            break;
          }
        }
      }

      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: lastError instanceof Error ? lastError.message : 'HTTP Request Pipeline Failed',
      });
      if (lastError instanceof Error) {
        span.recordException(lastError);
      }
      span.end();
      throw lastError;
    });
  }

  // --- Convenience Facade Methods ---
  public get<T>(url: string, headers?: Record<string, string>, options?: Partial<RequestConfig>) {
    return this.execute<T>({ method: HTTP_CONSTANTS.METHOD_GET, url, headers, ...options });
  }

  public post<T>(url: string, body: unknown, headers?: Record<string, string>, options?: Partial<RequestConfig>) {
    return this.execute<T>({ method: HTTP_CONSTANTS.METHOD_POST, url, body, headers, ...options });
  }

  public patch<T>(url: string, body: unknown, headers?: Record<string, string>, options?: Partial<RequestConfig>) {
    return this.execute<T>({ method: HTTP_CONSTANTS.METHOD_PATCH, url, body, headers, ...options });
  }

  public put<T>(url: string, body: unknown, headers?: Record<string, string>, options?: Partial<RequestConfig>) {
    return this.execute<T>({ method: HTTP_CONSTANTS.METHOD_PUT, url, body, headers, ...options });
  }

  public delete<T>(url: string, headers?: Record<string, string>, options?: Partial<RequestConfig>) {
    return this.execute<T>({ method: HTTP_CONSTANTS.METHOD_DELETE, url, headers, ...options });
  }
}

// Global Singleton Exported Client Engine
export const httpClient = new ScalableHttpClient();

export function getAuthHeaders(serviceSub = HTTP_CONSTANTS.DEFAULT_SERVICE_SUB): Record<string, string> {
  const secret = process.env.JWT_SECRET || HTTP_CONSTANTS.DEFAULT_JWT_SECRET;
  const header = { alg: HTTP_CONSTANTS.JWT_ALG, typ: HTTP_CONSTANTS.JWT_TYP };
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
    [HTTP_CONSTANTS.HEADER_CONTENT_TYPE]: HTTP_CONSTANTS.CONTENT_TYPE_JSON,
    [HTTP_CONSTANTS.HEADER_AUTHORIZATION]: `${HTTP_CONSTANTS.BEARER_PREFIX}${signingInput}.${signatureB64}`,
    [HTTP_CONSTANTS.HEADER_TRACEPARENT]: `00-${traceId}-${spanId}-01`,
    [HTTP_CONSTANTS.HEADER_X_TRACE_ID]: traceId,
  };
}

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

  const { data } = await httpClient.get<unknown>(url.toString(), undefined, { serviceSub });

  return transformOps
    ? (mapJson(data as Record<string, unknown>, transformOps) as unknown as T)
    : (data as T);
}
