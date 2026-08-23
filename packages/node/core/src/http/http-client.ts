import { RequestContextHolder } from '../tracing/request-context';

async function request<T = unknown>(
  method: string,
  url: string,
  body?: unknown,
  headers?: Record<string, string>,
): Promise<{ data: T; status: number; headers: Headers }> {
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

  const res = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...contextHeaders,
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const error = new HttpError(
      `${method} ${url} failed: ${res.status}`,
      res.status,
      res.headers.get('Retry-After'),
    );
    throw error;
  }

  const data = (await res.json()) as T;
  return { data, status: res.status, headers: res.headers };
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
