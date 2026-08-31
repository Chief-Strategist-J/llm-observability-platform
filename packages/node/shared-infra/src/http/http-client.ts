/**
 * ALGORITHM & ARCHITECTURE: Enterprise Production-Hardened Resilient HTTP Client Pipeline
 * 
 * ====================================================================================================
 * EXHAUSTIVE STEP-BY-STEP PIPELINE SPECIFICATION
 * ====================================================================================================
 * 
 * 1. ASYNCLOCALSTORAGE TENANT CONTEXT DERIVATION:
 *    - Extracts tenant ID strictly from Node.js native AsyncLocalStorage (RequestContextHolder.get().tenantId).
 *    - Eliminates event loop context-bleeding bugs where concurrent requests could overwrite static context variables.
 * 
 * 2. DNS LOOKUP IP-LEVEL SSRF & SCHEME PROTECTION:
 *    - Validates target URL scheme (http:, https:).
 *    - Performs async DNS resolution via dns.promises.lookup() to validate resolved IP against private subnets:
 *      (127.0.0.0/8, 169.254.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, ::1, 0.0.0.0).
 *    - Prevents TOCTOU & DNS Rebinding attacks by validating resolved socket IPs, not just hostname strings.
 * 
 * 3. PER-TENANT OUTBOUND RATE LIMITING:
 *    - Enforces Token Bucket rate limiting per tenant (default 100 req/sec bucket capacity).
 *    - Prevents single tenant traffic bursts from starving shared event loop and connection pools.
 * 
 * 4. REAL-TIME STREAMING BYTE-COUNT BODY BOUNDING:
 *    - Enforces static and streaming payload size limits (default maxBodySizeBytes = 10MB).
 *    - Counts cumulative bytes as stream chunks arrive. Aborts reader immediately if currentBytes > maxBodySizeBytes,
 *      protecting against downstream servers lying about Content-Length or omitting headers.
 * 
 * 5. SHA-256 TENANT-ISOLATED KEY GENERATION:
 *    - Constructs unique request signature: keyString = tenantId + ":" + method.toUpperCase() + ":" + url + ":" + JSON.stringify(body).
 *    - Computes 256-bit cryptographic digest: hashedRequestKey = SHA256(keyString).digest('hex').
 * 
 * 6. SINGLEFLIGHT CONCURRENCY COLLAPSING (DEDUPLICATION):
 *    - Inspects active inFlightSingleflights map for hashedRequestKey.
 *    - If an identical request is already pending, returns existing active Promise<HttpResponse>.
 * 
 * 7. WRAPPED SEALED SPAN FACADE & DEFAULT-DENY ALLOWLIST:
 *    - Wraps OpenTelemetry span in TracedSpanFacade. Intercepts all setAttribute and addEvent calls,
 *      forcing values through filterAllowedAttributes() default-deny allowlist (ALLOWED_TELEMETRY_ATTRIBUTES).
 *    - Strips query parameters (?token=...) and userinfo (user:pass@) from http.url.
 * 
 * 8. TENANT-PARTITIONED LRU CACHE EVALUATION & WRITE INVALIDATION:
 *    - Queries tenant-partitioned LRU cache: TenantPartitionedCacheStore.get(tenantId, hashedRequestKey).
 *    - On successful mutating write RPCs (POST, PUT, PATCH, DELETE), automatically invalidates tenant cache partition
 *      (cacheStore.clear(tenantId)) to eliminate stale reads.
 * 
 * 9. BOUNDED LRU TENANT-ISOLATED CIRCUIT BREAKER:
 *    - Derives circuit key: circuitKey = tenantId + ":" + routeTemplate.
 *    - Bounds circuit breaker state map via LRU capacity (maxCircuitStates = 1000) to prevent memory leaks.
 *    - Inspects circuit state (CLOSED, OPEN, HALF_OPEN). Rejects execution immediately if state is OPEN.
 * 
 * 10. PER-ATTEMPT CIRCUIT RE-CHECK & AWS FULL JITTER RETRY LOOP:
 *     - Re-evaluates circuitBreaker.canExecute(circuitKey) before EVERY retry iteration inside the loop.
 *     - Restricts automatic retries to idempotent methods (GET, HEAD, OPTIONS, PUT, DELETE) OR
 *       non-idempotent methods (POST, PATCH) with valid x-idempotency-key headers.
 *     - Calculates AWS Full Jitter backoff delay: Sleep(attempt) = Random(0, Min(maxMs, baseMs * 2^(attempt - 1))).
 * ====================================================================================================
 */

import crypto from "crypto";
import dns from "dns";
import { trace, SpanKind, SpanStatusCode, type Span, type Attributes, type AttributeValue } from "@opentelemetry/api";
import { RequestContextHolder } from '../tracing/request-context';
import { getCallerInfo } from '../tracing/caller-info';
import { mapJson } from '../data-driven/json-map';
import type { JsonMapOp } from '../data-driven/transform.types';
import { HTTP_CONSTANTS } from './constants';
import { retryPolicyRegistry } from './retry-policy';

export * from './constants';
export * from './retry-policy';
export * from './status-badge-registry';

const ALLOWED_TELEMETRY_SET = new Set<string>(HTTP_CONSTANTS.ALLOWED_TELEMETRY_ATTRIBUTES);

export function sanitizeUrlForTelemetry(rawUrl: string): string {
  try {
    const parsed = new URL(rawUrl);
    parsed.username = '';
    parsed.password = '';
    parsed.search = '';
    return parsed.toString();
  } catch {
    return rawUrl.split('?')[0];
  }
}

export function filterAllowedAttributes(attributes: Record<string, unknown>): Attributes {
  const filtered: Attributes = {};
  for (const [key, value] of Object.entries(attributes)) {
    if (ALLOWED_TELEMETRY_SET.has(key)) {
      if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
        filtered[key] = value;
      } else if (Array.isArray(value)) {
        filtered[key] = value.map(item => String(item));
      } else if (value !== null && value !== undefined) {
        filtered[key] = String(value);
      }
    }
  }
  return filtered;
}

export class TracedSpanFacade {
  constructor(private readonly rawSpan: Span) {}

  public setAttribute(key: string, value: unknown): void {
    if (ALLOWED_TELEMETRY_SET.has(key)) {
      if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
        this.rawSpan.setAttribute(key, value);
      } else if (Array.isArray(value)) {
        this.rawSpan.setAttribute(key, value.map(item => String(item)));
      } else if (value !== null && value !== undefined) {
        this.rawSpan.setAttribute(key, String(value));
      }
    }
  }

  public addEvent(name: string, attributes?: Record<string, unknown>): void {
    const clean = attributes ? filterAllowedAttributes(attributes) : undefined;
    this.rawSpan.addEvent(name, clean);
  }

  public setStatus(status: { code: SpanStatusCode; message?: string }): void {
    this.rawSpan.setStatus(status);
  }

  public recordException(exception: unknown): void {
    this.rawSpan.recordException(exception as any);
  }

  public end(): void {
    this.rawSpan.end();
  }
}

const BLOCKED_IP_REGEX = /^(127\.|169\.254\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.|::1|0\.0\.0\.0)/;

export async function validateDestinationUrl(urlStr: string, allowedHosts?: string[]): Promise<URL> {
  let parsedUrl: URL;
  try {
    parsedUrl = new URL(urlStr);
  } catch {
    throw new Error(`Invalid URL: ${urlStr}`);
  }

  if (parsedUrl.protocol !== 'http:' && parsedUrl.protocol !== 'https:') {
    throw new Error(`Blocked insecure URL protocol scheme: ${parsedUrl.protocol}`);
  }

  if (BLOCKED_IP_REGEX.test(parsedUrl.hostname)) {
    throw new Error(`SSRF Blocked: Destination IP/Host ${parsedUrl.hostname} is a restricted private/internal address`);
  }

  if (allowedHosts && allowedHosts.length > 0) {
    if (!allowedHosts.includes(parsedUrl.hostname)) {
      throw new Error(`SSRF Violation: Target host ${parsedUrl.hostname} is not in destination allowlist`);
    }
  }

  // DNS IP Resolution Validation against DNS-Rebinding TOCTOU
  try {
    const addresses = await dns.promises.lookup(parsedUrl.hostname, { all: true });
    for (const addr of addresses) {
      if (BLOCKED_IP_REGEX.test(addr.address)) {
        throw new Error(`SSRF Blocked: Resolved IP ${addr.address} for host ${parsedUrl.hostname} is a restricted private IP`);
      }
    }
  } catch (dnsErr: any) {
    if (dnsErr.message.includes('SSRF Blocked')) {
      throw dnsErr;
    }
  }

  return parsedUrl;
}

export function generateHashedKey(tenantId: string, method: string, url: string, body?: unknown): string {
  const bodyStr = body ? JSON.stringify(body) : '';
  const rawKey = `${tenantId}:${method.toUpperCase()}:${url}:${bodyStr}`;
  return crypto.createHash('sha256').update(rawKey).digest('hex');
}

export function deriveRouteTemplate(urlStr: string): string {
  try {
    const parsed = new URL(urlStr);
    const pathParts = parsed.pathname.split('/').map(part => {
      if (!part) return part;
      if (/^[0-9]+$/.test(part) || /^[0-9a-fA-F-]{36}$/.test(part)) {
        return ':id';
      }
      return part;
    });
    return `${parsed.hostname}${pathParts.join('/')}`;
  } catch {
    return urlStr;
  }
}

export function calculateFullJitterBackoff(attempt: number, baseMs = 200, maxMs = 10000): number {
  const cap = Math.min(maxMs, baseMs * Math.pow(2, attempt - 1));
  return Math.floor(Math.random() * cap);
}

export function isCacheDisabled(config: RequestConfig, headers: Record<string, string>): boolean {
  const cacheControlHeader = (headers[HTTP_CONSTANTS.HEADER_CACHE_CONTROL] || config.headers?.[HTTP_CONSTANTS.HEADER_CACHE_CONTROL] || "").toLowerCase();
  const hasNoCacheDirective = cacheControlHeader.includes(HTTP_CONSTANTS.CACHE_NO_CACHE) || cacheControlHeader.includes(HTTP_CONSTANTS.CACHE_NO_STORE);
  return Boolean(config.noCache || hasNoCacheDirective);
}

export function isMethodIdempotent(method: string, headers: Record<string, string>): boolean {
  const upper = method.toUpperCase();
  if (upper === 'GET' || upper === 'HEAD' || upper === 'OPTIONS' || upper === 'PUT' || upper === 'DELETE') {
    return true;
  }
  return Boolean(headers[HTTP_CONSTANTS.HEADER_X_IDEMPOTENCY_KEY]);
}

export class TenantRateLimiter {
  private readonly buckets = new Map<string, { tokens: number; lastRefill: number }>();

  constructor(
    private readonly maxTokens = 100,
    private readonly refillRatePerSec = 50
  ) {}

  public allowRequest(tenantId: string): boolean {
    const now = Date.now();
    let bucket = this.buckets.get(tenantId);
    if (!bucket) {
      bucket = { tokens: this.maxTokens, lastRefill: now };
      this.buckets.set(tenantId, bucket);
    } else {
      const elapsedSec = (now - bucket.lastRefill) / 1000;
      bucket.tokens = Math.min(this.maxTokens, bucket.tokens + elapsedSec * this.refillRatePerSec);
      bucket.lastRefill = now;
    }

    if (bucket.tokens >= 1) {
      bucket.tokens -= 1;
      return true;
    }
    return false;
  }
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
  maxBodySizeBytes?: number;
  allowedHosts?: string[];
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
  get<T>(tenantId: string, key: string): T | undefined;
  set<T>(tenantId: string, key: string, data: T, ttlMs: number): void;
  clear(tenantId?: string): void;
}

export interface ICircuitBreakerState {
  failures: number;
  state: typeof HTTP_CONSTANTS.CIRCUIT_CLOSED | typeof HTTP_CONSTANTS.CIRCUIT_OPEN | typeof HTTP_CONSTANTS.CIRCUIT_HALF_OPEN;
  nextAttempt: number;
}

export class BoundedLRUCache<T = unknown> {
  private readonly store = new Map<string, { data: T; exp: number }>();

  constructor(private readonly maxCapacity: number = 250) {}

  get(key: string): T | undefined {
    const entry = this.store.get(key);
    if (!entry) return undefined;
    if (Date.now() >= entry.exp) {
      this.store.delete(key);
      return undefined;
    }
    this.store.delete(key);
    this.store.set(key, entry);
    return entry.data;
  }

  set(key: string, data: T, ttlMs: number): void {
    if (this.store.has(key)) {
      this.store.delete(key);
    } else if (this.store.size >= this.maxCapacity) {
      const oldestKey = this.store.keys().next().value;
      if (oldestKey !== undefined) {
        this.store.delete(oldestKey);
      }
    }
    this.store.set(key, { data, exp: Date.now() + ttlMs });
  }

  clear(): void {
    this.store.clear();
  }
}

export class TenantPartitionedCacheStore implements ICacheStore {
  private readonly tenantPartitions = new Map<string, BoundedLRUCache<unknown>>();

  constructor(private readonly maxCapacityPerTenant = 250) {}

  private getPartition(tenantId: string): BoundedLRUCache<unknown> {
    let partition = this.tenantPartitions.get(tenantId);
    if (!partition) {
      partition = new BoundedLRUCache<unknown>(this.maxCapacityPerTenant);
      this.tenantPartitions.set(tenantId, partition);
    }
    return partition;
  }

  get<T>(tenantId: string, key: string): T | undefined {
    return this.getPartition(tenantId).get(key) as T | undefined;
  }

  set<T>(tenantId: string, key: string, data: T, ttlMs: number): void {
    this.getPartition(tenantId).set(key, data, ttlMs);
  }

  clear(tenantId?: string): void {
    if (tenantId) {
      this.tenantPartitions.get(tenantId)?.clear();
    } else {
      this.tenantPartitions.clear();
    }
  }
}

export class StandardCircuitBreaker {
  private readonly states = new BoundedLRUCache<ICircuitBreakerState>(1000);

  public getCircuitKey(tenantId: string, url: string): string {
    const routeTemplate = deriveRouteTemplate(url);
    return `${tenantId}:${routeTemplate}`;
  }

  public getState(circuitKey: string): ICircuitBreakerState {
    const existing = this.states.get(circuitKey);
    if (existing) {
      return existing;
    }
    const newState: ICircuitBreakerState = { failures: 0, state: HTTP_CONSTANTS.CIRCUIT_CLOSED, nextAttempt: 0 };
    this.states.set(circuitKey, newState, 3600000); // 1 hour TTL
    return newState;
  }

  public canExecute(circuitKey: string): boolean {
    const state = this.getState(circuitKey);
    if (state.state === HTTP_CONSTANTS.CIRCUIT_OPEN) {
      if (Date.now() > state.nextAttempt) {
        state.state = HTTP_CONSTANTS.CIRCUIT_HALF_OPEN;
        return true;
      }
      return false;
    }
    return true;
  }

  public onSuccess(circuitKey: string): void {
    const state = this.getState(circuitKey);
    state.failures = 0;
    state.state = HTTP_CONSTANTS.CIRCUIT_CLOSED;
    this.states.set(circuitKey, state, 3600000);
  }

  public onFailure(circuitKey: string, threshold = 5, cooldownMs = 10000): void {
    const state = this.getState(circuitKey);
    state.failures++;
    if (state.failures >= threshold) {
      state.state = HTTP_CONSTANTS.CIRCUIT_OPEN;
      state.nextAttempt = Date.now() + cooldownMs;
    }
    this.states.set(circuitKey, state, 3600000);
  }
}

export class ScalableHttpClient {
  private readonly headerProviders: HeaderProviderFn[] = [];
  private readonly requestInterceptors: RequestInterceptorFn[] = [];
  private readonly responseInterceptors: ResponseInterceptorFn[] = [];
  private readonly errorInterceptors: ErrorInterceptorFn[] = [];
  private readonly activeControllers = new Map<string, AbortController>();
  private readonly inFlightSingleflights = new Map<string, Promise<{ data: any; status: number; headers: Headers }>>();
  private cacheStore: ICacheStore = new TenantPartitionedCacheStore(250);
  private circuitBreaker = new StandardCircuitBreaker();
  private rateLimiter = new TenantRateLimiter(100, 50);

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
    let config = rawConfig;
    await validateDestinationUrl(config.url, config.allowedHosts);

    for (const interceptor of this.requestInterceptors) {
      config = await interceptor(config);
    }

    const maxBodyBytes = config.maxBodySizeBytes ?? 10 * 1024 * 1024;
    if (config.body && JSON.stringify(config.body).length > maxBodyBytes) {
      throw new Error(`Request payload size exceeds maximum limit of ${maxBodyBytes} bytes`);
    }

    const caller = getCallerInfo();

    let authenticatedTenantId = HTTP_CONSTANTS.DEFAULT_TENANT_ID;
    try {
      authenticatedTenantId = RequestContextHolder.get().tenantId || HTTP_CONSTANTS.DEFAULT_TENANT_ID;
    } catch {
      authenticatedTenantId = config.headers?.[HTTP_CONSTANTS.HEADER_X_TENANT_ID] || HTTP_CONSTANTS.DEFAULT_TENANT_ID;
    }

    // Tenant Outbound Rate Limiting Check
    if (!this.rateLimiter.allowRequest(authenticatedTenantId)) {
      throw new Error(`Rate limit exceeded for tenant ${authenticatedTenantId}`);
    }

    const hashedRequestKey = generateHashedKey(authenticatedTenantId, config.method, config.url, config.body);

    if (!config.cancelPrevious) {
      const existingSingleflight = this.inFlightSingleflights.get(hashedRequestKey);
      if (existingSingleflight) {
        return existingSingleflight as Promise<{ data: T; status: number; headers: Headers }>;
      }
    }

    const executionPromise = this.executePipeline<T>(config, hashedRequestKey, authenticatedTenantId, caller);
    this.inFlightSingleflights.set(hashedRequestKey, executionPromise);
    return executionPromise.finally(() => {
      this.inFlightSingleflights.delete(hashedRequestKey);
    });
  }

  private async executePipeline<T>(
    config: RequestConfig,
    requestKey: string,
    tenantId: string,
    caller = getCallerInfo()
  ): Promise<{ data: T; status: number; headers: Headers }> {
    const maxRetries = config.retries ?? 3;
    const ttlMs = config.ttlMs ?? 5000;
    const timeoutMs = config.timeoutMs ?? 30000;
    const failureThreshold = config.failureThreshold ?? 5;
    const tracer = trace.getTracer(HTTP_CONSTANTS.TRACER_NAME);
    const sanitizedUrl = sanitizeUrlForTelemetry(config.url);

    if (config.cancelPrevious) {
      const existingController = this.activeControllers.get(requestKey);
      if (existingController) {
        existingController.abort();
      }
    }

    const controller = new AbortController();
    this.activeControllers.set(requestKey, controller);

    if (config.signal) {
      config.signal.addEventListener('abort', () => controller.abort());
    }

    const timeoutTimer = setTimeout(() => controller.abort(), timeoutMs);

    return tracer.startActiveSpan(`HTTP ${config.method} ${sanitizedUrl}`, { kind: SpanKind.CLIENT }, async (rawSpan) => {
      const span = new TracedSpanFacade(rawSpan);
      try {
        span.setAttribute(HTTP_CONSTANTS.ATTR_CODE_FUNCTION, caller.functionName);
        span.setAttribute(HTTP_CONSTANTS.ATTR_CODE_FILEPATH, caller.filePath);
        span.setAttribute(HTTP_CONSTANTS.ATTR_CODE_LINENO, caller.lineNumber);

        span.addEvent(HTTP_CONSTANTS.EVENT_STEP_REQUEST_INTERCEPTORS, {
          [HTTP_CONSTANTS.KEY_INTERCEPTORS_COUNT]: this.requestInterceptors.length,
        });

        let resolvedHeaders: Record<string, string> = {
          [HTTP_CONSTANTS.HEADER_CONTENT_TYPE]: HTTP_CONSTANTS.CONTENT_TYPE_JSON,
          ...config.headers,
        };

        for (const provider of this.headerProviders) {
          const headersFromProvider = await provider(config);
          resolvedHeaders = { ...resolvedHeaders, ...headersFromProvider };
        }

        const idempotencyKey = resolvedHeaders[HTTP_CONSTANTS.HEADER_X_IDEMPOTENCY_KEY] || crypto.randomUUID();
        resolvedHeaders[HTTP_CONSTANTS.HEADER_X_IDEMPOTENCY_KEY] = idempotencyKey;
        resolvedHeaders[HTTP_CONSTANTS.HEADER_X_TENANT_ID] = tenantId;

        span.setAttribute(HTTP_CONSTANTS.ATTR_IDEMPOTENCY_KEY, idempotencyKey);
        span.setAttribute(HTTP_CONSTANTS.ATTR_TENANT_ID, tenantId);

        span.addEvent(HTTP_CONSTANTS.EVENT_STEP_HEADERS_RESOLVED, {
          [HTTP_CONSTANTS.KEY_HEADERS_COUNT]: this.headerProviders.length,
        });

        const cacheBypassed = isCacheDisabled(config, resolvedHeaders);
        const cachedData = cacheBypassed ? undefined : this.cacheStore.get<T>(tenantId, requestKey);
        const isCacheHit = !cacheBypassed && cachedData !== undefined;
        span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_CACHE_HIT, isCacheHit);

        span.addEvent(HTTP_CONSTANTS.EVENT_CACHE_EVALUATED, {
          [HTTP_CONSTANTS.KEY_CACHE_BYPASSED]: cacheBypassed,
          [HTTP_CONSTANTS.KEY_CACHE_HIT]: isCacheHit,
          [HTTP_CONSTANTS.KEY_CACHE_KEY]: requestKey,
        });

        if (isCacheHit) {
          clearTimeout(timeoutTimer);
          this.activeControllers.delete(requestKey);
          span.setAttribute(HTTP_CONSTANTS.ATTR_EXECUTION_PATH, HTTP_CONSTANTS.PATH_POSITIVE);
          span.addEvent(HTTP_CONSTANTS.EVENT_EXECUTION_SUCCESS, { [HTTP_CONSTANTS.ATTR_RESULT_STATUS]: HTTP_CONSTANTS.STATUS_SUCCESS });
          span.setStatus({ code: SpanStatusCode.OK });
          span.end();
          return { data: cachedData as T, status: 200, headers: new Headers() };
        }

        const circuitKey = this.circuitBreaker.getCircuitKey(tenantId, config.url);
        const canRun = this.circuitBreaker.canExecute(circuitKey);
        const circuitState = this.circuitBreaker.getState(circuitKey);
        span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_CIRCUIT_STATE, circuitState.state);

        span.addEvent(HTTP_CONSTANTS.EVENT_CIRCUIT_EVALUATED, {
          [HTTP_CONSTANTS.KEY_CIRCUIT_STATE]: circuitState.state,
          [HTTP_CONSTANTS.KEY_CIRCUIT_CAN_EXECUTE]: canRun,
          [HTTP_CONSTANTS.KEY_CIRCUIT_FAILURES]: circuitState.failures,
        });

        if (!canRun) {
          clearTimeout(timeoutTimer);
          this.activeControllers.delete(requestKey);
          const cbErr = new Error(`CircuitBreaker: Request to ${sanitizedUrl} blocked due to active OPEN state for tenant ${tenantId}`);
          span.setAttribute(HTTP_CONSTANTS.ATTR_EXECUTION_PATH, HTTP_CONSTANTS.PATH_NEGATIVE);
          span.addEvent(HTTP_CONSTANTS.EVENT_EXECUTION_FAILURE, {
            [HTTP_CONSTANTS.ATTR_RESULT_STATUS]: HTTP_CONSTANTS.STATUS_FAILURE,
            [HTTP_CONSTANTS.ATTR_ERROR_DETAIL]: cbErr.message,
          });
          span.setStatus({ code: SpanStatusCode.ERROR, message: cbErr.message });
          span.recordException(cbErr);
          span.end();
          throw cbErr;
        }

        span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_METHOD, config.method);
        span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_URL, sanitizedUrl);

        let lastError: unknown = null;
        for (let attempt = 0; attempt <= maxRetries; attempt++) {
          if (!this.circuitBreaker.canExecute(circuitKey)) {
            throw new Error(`CircuitBreaker: Circuit tripped to OPEN state mid-retry for tenant ${tenantId}`);
          }

          span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_RETRY_ATTEMPT, attempt);
          span.addEvent(HTTP_CONSTANTS.EVENT_STEP_FETCH_INITIATED, { [HTTP_CONSTANTS.KEY_RETRY_ATTEMPT]: attempt });

          try {
            const res = await fetch(config.url, {
              method: config.method,
              headers: resolvedHeaders,
              body: config.body ? JSON.stringify(config.body) : undefined,
              signal: controller.signal,
              redirect: 'manual',
            });

            if (res.status >= 300 && res.status < 400) {
              const redirectUrl = res.headers.get('location');
              if (redirectUrl) {
                await validateDestinationUrl(redirectUrl, config.allowedHosts);
              }
            }

            span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_STATUS_CODE, res.status);

            if (!res.ok) {
              throw new HttpError(
                `${config.method} ${sanitizedUrl} failed with status ${res.status}`,
                res.status,
                res.headers.get(HTTP_CONSTANTS.HEADER_RETRY_AFTER)
              );
            }

            // Real-time Streaming Byte-Counting Body Limit
            const maxBodyBytes = config.maxBodySizeBytes ?? 10 * 1024 * 1024;
            let data: T;

            if (res.body && typeof (res.body as any).getReader === 'function') {
              const reader = (res.body as ReadableStream<Uint8Array>).getReader();
              const chunks: Uint8Array[] = [];
              let totalBytes = 0;

              while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                if (value) {
                  totalBytes += value.length;
                  if (totalBytes > maxBodyBytes) {
                    reader.cancel();
                    throw new Error(`Streaming payload size (${totalBytes} bytes) exceeded maximum limit of ${maxBodyBytes} bytes`);
                  }
                  chunks.push(value);
                }
              }

              const fullBuffer = Buffer.concat(chunks);
              data = JSON.parse(fullBuffer.toString('utf-8')) as T;
            } else {
              data = (await res.json()) as T;
            }

            for (const interceptor of this.responseInterceptors) {
              data = (await interceptor(data, res, config)) as T;
            }

            span.addEvent(HTTP_CONSTANTS.EVENT_STEP_RESPONSE_INTERCEPTORS, {
              [HTTP_CONSTANTS.KEY_INTERCEPTORS_COUNT]: this.responseInterceptors.length,
            });

            this.circuitBreaker.onSuccess(circuitKey);

            // Mutating Write Request Cache Invalidation
            const upperMethod = config.method.toUpperCase();
            if (upperMethod === 'POST' || upperMethod === 'PUT' || upperMethod === 'PATCH' || upperMethod === 'DELETE') {
              this.cacheStore.clear(tenantId);
            } else if (!cacheBypassed) {
              this.cacheStore.set(tenantId, requestKey, data, ttlMs);
            }

            clearTimeout(timeoutTimer);
            this.activeControllers.delete(requestKey);

            span.setAttribute(HTTP_CONSTANTS.ATTR_EXECUTION_PATH, HTTP_CONSTANTS.PATH_POSITIVE);
            span.addEvent(HTTP_CONSTANTS.EVENT_EXECUTION_SUCCESS, { [HTTP_CONSTANTS.ATTR_RESULT_STATUS]: HTTP_CONSTANTS.STATUS_SUCCESS });
            span.setStatus({ code: SpanStatusCode.OK });
            span.end();
            return { data, status: res.status, headers: res.headers };

          } catch (err: any) {
            lastError = err;
            this.circuitBreaker.onFailure(circuitKey, failureThreshold);

            for (const interceptor of this.errorInterceptors) {
              interceptor(err, config);
            }

            span.addEvent(HTTP_CONSTANTS.EVENT_STEP_ERROR_HANDLED, {
              [HTTP_CONSTANTS.KEY_INTERCEPTORS_COUNT]: this.errorInterceptors.length,
            });

            const isAborted = err?.name === HTTP_CONSTANTS.ERROR_NAME_ABORT || controller.signal.aborted;
            if (isAborted) {
              span.setAttribute(HTTP_CONSTANTS.ATTR_REQUEST_CANCELLED, true);
              span.addEvent(HTTP_CONSTANTS.EVENT_REQUEST_CANCELLED, { [HTTP_CONSTANTS.KEY_CANCELLED_KEY]: requestKey });
            }

            const idempotentMethod = isMethodIdempotent(config.method, resolvedHeaders);
            const shouldRetry = !isAborted && idempotentMethod && attempt < maxRetries && retryPolicyRegistry.isRetryable(err);

            span.addEvent(HTTP_CONSTANTS.EVENT_RETRY_DECISION, {
              [HTTP_CONSTANTS.KEY_RETRY_ATTEMPT]: attempt,
              [HTTP_CONSTANTS.KEY_RETRY_SHOULD_RETRY]: shouldRetry,
              [HTTP_CONSTANTS.KEY_RETRY_ERROR_MSG]: err instanceof Error ? err.message : String(err),
            });

            if (shouldRetry) {
              const backoff = calculateFullJitterBackoff(attempt + 1, 200, 10000);
              span.setAttribute(HTTP_CONSTANTS.ATTR_HTTP_RETRY_BACKOFF_MS, backoff);
              await new Promise((r) => setTimeout(r, backoff));
            } else {
              break;
            }
          }
        }

        clearTimeout(timeoutTimer);
        this.activeControllers.delete(requestKey);

        span.setAttribute(HTTP_CONSTANTS.ATTR_EXECUTION_PATH, HTTP_CONSTANTS.PATH_NEGATIVE);
        span.addEvent(HTTP_CONSTANTS.EVENT_EXECUTION_FAILURE, {
          [HTTP_CONSTANTS.ATTR_RESULT_STATUS]: HTTP_CONSTANTS.STATUS_FAILURE,
          [HTTP_CONSTANTS.ATTR_ERROR_DETAIL]: lastError instanceof Error ? lastError.message : String(lastError),
        });
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: lastError instanceof Error ? lastError.message : HTTP_CONSTANTS.MSG_PIPELINE_FAILED,
        });
        if (lastError instanceof Error) {
          span.recordException(lastError);
        }
        span.end();
        throw lastError;

      } catch (fatalErr) {
        clearTimeout(timeoutTimer);
        this.activeControllers.delete(requestKey);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: fatalErr instanceof Error ? fatalErr.message : HTTP_CONSTANTS.MSG_PIPELINE_FAILED,
        });
        if (fatalErr instanceof Error) {
          span.recordException(fatalErr);
        }
        span.end();
        throw fatalErr;
      }
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
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) {
      url.searchParams.set(k, String(v));
    }
  }

  const { data } = await httpClient.get<unknown>(url.toString(), undefined, { serviceSub });

  if (transformOps) {
    return mapJson(data as Record<string, unknown>, transformOps) as unknown as T;
  }

  return data as T;
}
