/**
 * ALGORITHM & ARCHITECTURE: Scalable Resilient HTTP Client Pipeline with Granular Step-by-Step Telemetry
 * 
 * 1. Step 1 (Request Interception): Config passes through registered RequestInterceptors via Promise.reduce. Emits EVENT_STEP_REQUEST_INTERCEPTORS.
 * 2. Step 2 (Singleflight & Cancellation): Collapses identical concurrent read requests (Singleflight pattern) to prevent thundering herd; aborts previous request via AbortController if cancelPrevious is true. Emits EVENT_STEP_SINGLEFLIGHT_CHECK.
 * 3. Step 3 (Header Resolution): Aggregates headers from HeaderProviderRegistry (Auth JWT, W3C traceparent, Tenant ID, Cache-Control). Emits EVENT_STEP_HEADERS_RESOLVED.
 * 4. Step 4 (Idempotency Key Preservation): Preserves identical x-idempotency-key across all retry attempts for idempotent downstream processing.
 * 5. Step 5 (Cache Policy Evaluation): Evaluates Cache-Control headers (no-cache, no-store) and config.noCache flag with Decision Span Events.
 * 6. Step 6 (Circuit Breaker Inspection): Evaluates ICircuitBreaker status; rejects execution if state is OPEN with Decision Span Events.
 * 7. Step 7 (Timeout & Signal Merging): Integrates request timeout (timeoutMs) and merges caller-provided AbortSignal.
 * 8. Step 8 (Recursive Retry Pipeline with Dual Positive & Negative Path Tracing & Step Telemetry):
 *    a. Invokes fetch with merged AbortSignal and exponential Full Jitter backoff calculation. Emits EVENT_STEP_FETCH_INITIATED.
 *    b. On HTTP failure, queries RetryPolicyRegistry to verify error retryability. Emits EVENT_STEP_ERROR_HANDLED.
 *    c. On HTTP success, executes ResponseInterceptors, resets Circuit Breaker, updates CacheStore (if enabled). Emits EVENT_STEP_RESPONSE_INTERCEPTORS and EVENT_EXECUTION_SUCCESS.
 *    d. On error, triggers ErrorInterceptors, OpenTelemetry exception recording, and EVENT_EXECUTION_FAILURE.
 */

import crypto from "crypto";
import { trace, SpanKind, SpanStatusCode } from "@opentelemetry/api";
import { RequestContextHolder } from '../tracing/request-context';
import { mapJson } from '../data-driven/json-map';
import type { JsonMapOp } from '../data-driven/transform.types';
import { HTTP_CONSTANTS } from './constants';
import { retryPolicyRegistry } from './retry-policy';

export * from './constants';
export * from './retry-policy';
export * from './status-badge-registry';

export function calculateFullJitterBackoff(attempt: number, baseMs = 200, maxMs = 10000): number {
  const cap = Math.min(maxMs, baseMs * Math.pow(2, attempt - 1));
  return Math.floor(Math.random() * cap);
}

export function isCacheDisabled(config: RequestConfig, headers: Record<string, string>): boolean {
  const cacheControlHeader = (headers[HTTP_CONSTANTS.HEADER_CACHE_CONTROL] || config.headers?.[HTTP_CONSTANTS.HEADER_CACHE_CONTROL] || "").toLowerCase();
  const hasNoCacheDirective = cacheControlHeader.includes(HTTP_CONSTANTS.CACHE_NO_CACHE) || cacheControlHeader.includes(HTTP_CONSTANTS.CACHE_NO_STORE);
  return Boolean(config.noCache || hasNoCacheDirective);
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
  timeoutMs?: number;
  failureThreshold?: number;
  noCache?: boolean;
  cancelPrevious?: boolean;
  signal?: AbortSignal;
}

export type HeaderProviderFn = (config: RequestConfig) => Record<string, string> | Promise<Record<string, string>>;
export type RequestInterceptorFn = (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
export type ResponseInterceptorFn<T = any> = (data: T, response: Response, config: RequestConfig) => T | Promise<T>;
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

export class InMemoryCacheStore implements ICacheStore {
  private readonly store = new Map<string, { data: unknown; exp: number }>();

  get<T>(key: string): T | undefined {
    const entry = this.store.get(key);
    return entry && Date.now() < entry.exp ? (entry.data as T) : undefined;
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
    const existing = this.states.get(url);
    return existing ?? (() => {
      const newState: ICircuitBreakerState = { failures: 0, state: HTTP_CONSTANTS.CIRCUIT_CLOSED, nextAttempt: 0 };
      this.states.set(url, newState);
      return newState;
    })();
  }

  public canExecute(url: string): boolean {
    const state = this.getState(url);
    return state.state === HTTP_CONSTANTS.CIRCUIT_OPEN
      ? Date.now() > state.nextAttempt
        ? ((state.state = HTTP_CONSTANTS.CIRCUIT_HALF_OPEN), true)
        : false
      : true;
  }

  public onSuccess(url: string): void {
    const state = this.getState(url);
    state.failures = 0;
    state.state = HTTP_CONSTANTS.CIRCUIT_CLOSED;
  }

  public onFailure(url: string, threshold = 5, cooldownMs = 10000): void {
    const state = this.getState(url);
    state.failures++;
    state.failures >= threshold && ((state.state = HTTP_CONSTANTS.CIRCUIT_OPEN), (state.nextAttempt = Date.now() + cooldownMs));
  }
}

export class ScalableHttpClient {
  private readonly headerProviders: HeaderProviderFn[] = [];
  private readonly requestInterceptors: RequestInterceptorFn[] = [];
  private readonly responseInterceptors: ResponseInterceptorFn[] = [];
  private readonly errorInterceptors: ErrorInterceptorFn[] = [];
  private readonly activeControllers = new Map<string, AbortController>();
  private readonly inFlightSingleflights = new Map<string, Promise<{ data: any; status: number; headers: Headers }>>();
  private cacheStore: ICacheStore = new InMemoryCacheStore();
  private circuitBreaker = new StandardCircuitBreaker();

  constructor() {
    this.registerDefaultHeaderProviders();
  }

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

  private registerDefaultHeaderProviders(): void {
    this.registerHeaderProvider((config) =>
      getAuthHeaders(config.serviceSub || HTTP_CONSTANTS.DEFAULT_SERVICE_SUB)
    );

    this.registerHeaderProvider((): Record<string, string> => {
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

  public async execute<T>(rawConfig: RequestConfig): Promise<{ data: T; status: number; headers: Headers }> {
    const config = await this.requestInterceptors.reduce(
      async (accPromise, interceptor) => interceptor(await accPromise),
      Promise.resolve(rawConfig)
    );

    const requestKey = `${config.method}:${config.url}:${config.body ? JSON.stringify(config.body) : ''}`;

    const existingSingleflight = !config.cancelPrevious && this.inFlightSingleflights.get(requestKey);
    return existingSingleflight
      ? (existingSingleflight as Promise<{ data: T; status: number; headers: Headers }>)
      : await (async () => {
          const executionPromise = this.executePipeline<T>(config, requestKey);
          this.inFlightSingleflights.set(requestKey, executionPromise);
          return executionPromise.finally(() => this.inFlightSingleflights.delete(requestKey));
        })();
  }

  private async executePipeline<T>(config: RequestConfig, requestKey: string): Promise<{ data: T; status: number; headers: Headers }> {
    const maxRetries = config.retries ?? 3;
    const ttlMs = config.ttlMs ?? 5000;
    const timeoutMs = config.timeoutMs ?? 30000;
    const failureThreshold = config.failureThreshold ?? 5;
    const tracer = trace.getTracer(HTTP_CONSTANTS.TRACER_NAME);

    const existingController = this.activeControllers.get(requestKey);
    config.cancelPrevious && existingController && existingController.abort();

    const controller = new AbortController();
    this.activeControllers.set(requestKey, controller);

    config.signal && config.signal.addEventListener('abort', () => controller.abort());

    const timeoutTimer = setTimeout(() => controller.abort(), timeoutMs);

    return tracer.startActiveSpan(`HTTP ${config.method} ${config.url}`, { kind: SpanKind.CLIENT }, async (span) => {
      // Step 1 Telemetry: Request Interceptors
      span.addEvent(HTTP_CONSTANTS.EVENT_STEP_REQUEST_INTERCEPTORS, {
        [HTTP_CONSTANTS.KEY_INTERCEPTORS_COUNT]: this.requestInterceptors.length,
      });

      // Step 2 Telemetry: Header Providers Resolution
      const resolvedHeaders = await this.headerProviders.reduce<Promise<Record<string, string>>>(
        async (accPromise, provider) => ({
          ...(await accPromise),
          ...(await provider(config)),
        }),
        Promise.resolve<Record<string, string>>({
          [HTTP_CONSTANTS.HEADER_CONTENT_TYPE]: HTTP_CONSTANTS.CONTENT_TYPE_JSON,
          ...config.headers,
        })
      );

      span.addEvent(HTTP_CONSTANTS.EVENT_STEP_HEADERS_RESOLVED, {
        [HTTP_CONSTANTS.KEY_HEADERS_COUNT]: this.headerProviders.length,
      });

      const idempotencyKey = resolvedHeaders[HTTP_CONSTANTS.HEADER_X_IDEMPOTENCY_KEY] || crypto.randomBytes(16).toString("hex");
      resolvedHeaders[HTTP_CONSTANTS.HEADER_X_IDEMPOTENCY_KEY] = idempotencyKey;
      span.setAttribute(HTTP_CONSTANTS.ATTR_IDEMPOTENCY_KEY, idempotencyKey);

      // Step 3 Telemetry: Cache Policy Evaluation
      const cacheBypassed = isCacheDisabled(config, resolvedHeaders);
      const cachedData = cacheBypassed ? undefined : this.cacheStore.get<T>(requestKey);
      const isCacheHit = !cacheBypassed && cachedData !== undefined;
      span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_CACHE_HIT, isCacheHit);

      span.addEvent(HTTP_CONSTANTS.EVENT_CACHE_EVALUATED, {
        [HTTP_CONSTANTS.KEY_CACHE_BYPASSED]: cacheBypassed,
        [HTTP_CONSTANTS.KEY_CACHE_HIT]: isCacheHit,
        [HTTP_CONSTANTS.KEY_CACHE_KEY]: requestKey,
      });

      // Positive Path: Cache Hit Resolution
      return isCacheHit
        ? (
            clearTimeout(timeoutTimer),
            this.activeControllers.delete(requestKey),
            span.setAttribute(HTTP_CONSTANTS.ATTR_EXECUTION_PATH, HTTP_CONSTANTS.PATH_POSITIVE),
            span.addEvent(HTTP_CONSTANTS.EVENT_EXECUTION_SUCCESS, { [HTTP_CONSTANTS.ATTR_RESULT_STATUS]: HTTP_CONSTANTS.STATUS_SUCCESS }),
            span.setStatus({ code: SpanStatusCode.OK }),
            span.end(),
            { data: cachedData, status: 200, headers: new Headers() }
          )
        : await (async () => {
            // Step 4 Telemetry: Circuit Breaker Inspection
            const canRun = this.circuitBreaker.canExecute(config.url);
            const circuitState = this.circuitBreaker.getState(config.url);
            span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_CIRCUIT_STATE, circuitState.state);

            span.addEvent(HTTP_CONSTANTS.EVENT_CIRCUIT_EVALUATED, {
              [HTTP_CONSTANTS.KEY_CIRCUIT_STATE]: circuitState.state,
              [HTTP_CONSTANTS.KEY_CIRCUIT_CAN_EXECUTE]: canRun,
              [HTTP_CONSTANTS.KEY_CIRCUIT_FAILURES]: circuitState.failures,
            });

            // Negative Path: Circuit Breaker Rejection
            return !canRun
              ? (() => {
                  clearTimeout(timeoutTimer);
                  this.activeControllers.delete(requestKey);
                  const cbErr = new Error(`CircuitBreaker: Request to ${config.url} blocked due to active OPEN state.`);
                  span.setAttribute(HTTP_CONSTANTS.ATTR_EXECUTION_PATH, HTTP_CONSTANTS.PATH_NEGATIVE);
                  span.addEvent(HTTP_CONSTANTS.EVENT_EXECUTION_FAILURE, {
                    [HTTP_CONSTANTS.ATTR_RESULT_STATUS]: HTTP_CONSTANTS.STATUS_FAILURE,
                    [HTTP_CONSTANTS.ATTR_ERROR_DETAIL]: cbErr.message,
                  });
                  span.setStatus({ code: SpanStatusCode.ERROR, message: cbErr.message });
                  span.recordException(cbErr);
                  span.end();
                  throw cbErr;
                })()
              : await (async () => {
                  span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_METHOD, config.method);
                  span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_URL, config.url);
                  resolvedHeaders[HTTP_CONSTANTS.HEADER_X_TENANT_ID] &&
                    span.setAttribute(HTTP_CONSTANTS.ATTR_TENANT_ID, resolvedHeaders[HTTP_CONSTANTS.HEADER_X_TENANT_ID]!);

                  // Pure Recursive Retry Pipeline with Step & Decision Telemetry
                  const attemptFetch = async (attempt: number): Promise<{ data: T; status: number; headers: Headers }> => {
                    span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_RETRY_ATTEMPT, attempt);
                    span.addEvent(HTTP_CONSTANTS.EVENT_STEP_FETCH_INITIATED, { [HTTP_CONSTANTS.KEY_RETRY_ATTEMPT]: attempt });

                    try {
                      const res = await fetch(config.url, {
                        method: config.method,
                        headers: resolvedHeaders,
                        body: config.body ? JSON.stringify(config.body) : undefined,
                        signal: controller.signal,
                      });

                      span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_STATUS_CODE, res.status);

                      return !res.ok
                        ? (() => {
                            throw new HttpError(
                              `${config.method} ${config.url} failed with status ${res.status}`,
                              res.status,
                              res.headers.get(HTTP_CONSTANTS.HEADER_RETRY_AFTER)
                            );
                          })()
                        : await (async () => {
                            const rawJson = (await res.json()) as T;
                            const data = (await this.responseInterceptors.reduce<Promise<unknown>>(
                              async (accPromise, interceptor) => interceptor(await accPromise, res, config),
                              Promise.resolve(rawJson)
                            )) as T;

                            span.addEvent(HTTP_CONSTANTS.EVENT_STEP_RESPONSE_INTERCEPTORS, {
                              [HTTP_CONSTANTS.KEY_INTERCEPTORS_COUNT]: this.responseInterceptors.length,
                            });

                            this.circuitBreaker.onSuccess(config.url);
                            !cacheBypassed && this.cacheStore.set(requestKey, data, ttlMs);
                            clearTimeout(timeoutTimer);
                            this.activeControllers.delete(requestKey);

                            // Positive Path: Network Success Resolution
                            span.setAttribute(HTTP_CONSTANTS.ATTR_EXECUTION_PATH, HTTP_CONSTANTS.PATH_POSITIVE);
                            span.addEvent(HTTP_CONSTANTS.EVENT_EXECUTION_SUCCESS, { [HTTP_CONSTANTS.ATTR_RESULT_STATUS]: HTTP_CONSTANTS.STATUS_SUCCESS });
                            span.setStatus({ code: SpanStatusCode.OK });
                            return { data, status: res.status, headers: res.headers };
                          })();
                    } catch (err: any) {
                      this.circuitBreaker.onFailure(config.url, failureThreshold);
                      this.errorInterceptors.forEach((interceptor) => interceptor(err, config));

                      span.addEvent(HTTP_CONSTANTS.EVENT_STEP_ERROR_HANDLED, {
                        [HTTP_CONSTANTS.KEY_INTERCEPTORS_COUNT]: this.errorInterceptors.length,
                      });

                      const isAborted = err?.name === HTTP_CONSTANTS.ERROR_NAME_ABORT || controller.signal.aborted;
                      isAborted && (span.setAttribute(HTTP_CONSTANTS.ATTR_REQUEST_CANCELLED, true), span.addEvent(HTTP_CONSTANTS.EVENT_REQUEST_CANCELLED, { [HTTP_CONSTANTS.KEY_CANCELLED_KEY]: requestKey }));

                      const shouldRetry = !isAborted && attempt < maxRetries && retryPolicyRegistry.isRetryable(err);

                      span.addEvent(HTTP_CONSTANTS.EVENT_RETRY_DECISION, {
                        [HTTP_CONSTANTS.KEY_RETRY_ATTEMPT]: attempt,
                        [HTTP_CONSTANTS.KEY_RETRY_SHOULD_RETRY]: shouldRetry,
                        [HTTP_CONSTANTS.KEY_RETRY_ERROR_MSG]: err instanceof Error ? err.message : String(err),
                      });

                      return shouldRetry
                        ? await (async () => {
                            const backoff = calculateFullJitterBackoff(attempt + 1, 200, 10000);
                            span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_RETRY_BACKOFF_MS, backoff);
                            await new Promise((r) => setTimeout(r, backoff));
                            return attemptFetch(attempt + 1);
                          })()
                        : (() => {
                            clearTimeout(timeoutTimer);
                            this.activeControllers.delete(requestKey);

                            // Negative Path: Network Failure / Retry Exhaustion Resolution
                            span.setAttribute(HTTP_CONSTANTS.ATTR_EXECUTION_PATH, HTTP_CONSTANTS.PATH_NEGATIVE);
                            span.addEvent(HTTP_CONSTANTS.EVENT_EXECUTION_FAILURE, {
                              [HTTP_CONSTANTS.ATTR_RESULT_STATUS]: HTTP_CONSTANTS.STATUS_FAILURE,
                              [HTTP_CONSTANTS.ATTR_ERROR_DETAIL]: err instanceof Error ? err.message : String(err),
                            });
                            span.setStatus({
                              code: SpanStatusCode.ERROR,
                              message: err instanceof Error ? err.message : HTTP_CONSTANTS.MSG_PIPELINE_FAILED,
                            });
                            err instanceof Error && span.recordException(err);
                            span.end();
                            throw err;
                          })();
                    }
                  };

                  return attemptFetch(0);
                })();
          })();
    });
  }

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

export const httpClient = new ScalableHttpClient();

export function getAuthHeaders(serviceSub: string = HTTP_CONSTANTS.DEFAULT_SERVICE_SUB): Record<string, string> {
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
    v !== undefined && v !== null && url.searchParams.set(k, String(v));
  });

  const { data } = await httpClient.get<unknown>(url.toString(), undefined, { serviceSub });

  return transformOps
    ? (mapJson(data as Record<string, unknown>, transformOps) as unknown as T)
    : (data as T);
}
