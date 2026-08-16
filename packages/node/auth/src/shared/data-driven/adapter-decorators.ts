import { trace } from '@opentelemetry/api';

export function withRetry<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  retries = 3,
  delayMs = 100
): T {
  return (async (...args: Parameters<T>) => {
    let lastErr: unknown;
    for (let i = 0; i < retries; i++) {
      try {
        return await fn(...args);
      } catch (err) {
        lastErr = err;
        if (i < retries - 1) {
          await new Promise((res) => setTimeout(res, delayMs * Math.pow(2, i)));
        }
      }
    }
    throw lastErr;
  }) as T;
}

export function withCache<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  ttlMs = 5000
): T {
  const cache = new Map<string, { value: any; expires: number }>();
  return (async (...args: Parameters<T>) => {
    const key = JSON.stringify(args);
    const cached = cache.get(key);
    if (cached && cached.expires > Date.now()) {
      return cached.value;
    }
    const result = await fn(...args);
    cache.set(key, { value: result, expires: Date.now() + ttlMs });
    return result;
  }) as T;
}

export function withCircuitBreaker<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  failureThreshold = 5,
  cooldownMs = 10000
): T {
  let failures = 0;
  let nextAttempt = 0;

  return (async (...args: Parameters<T>) => {
    if (failures >= failureThreshold) {
      if (Date.now() < nextAttempt) {
        throw new Error('Circuit breaker open');
      }
      failures = 0;
    }
    try {
      const res = await fn(...args);
      failures = 0;
      return res;
    } catch (err) {
      failures++;
      if (failures >= failureThreshold) {
        nextAttempt = Date.now() + cooldownMs;
      }
      throw err;
    }
  }) as T;
}

export function withTracing<T extends (...args: any[]) => Promise<any>>(
  name: string,
  fn: T
): T {
  return (async (...args: Parameters<T>) => {
    const tracer = trace.getTracer('auth-adapter');
    return tracer.startActiveSpan(name, async (span) => {
      try {
        const result = await fn(...args);
        span.end();
        return result;
      } catch (err) {
        span.recordException(err as Error);
        span.end();
        throw err;
      }
    });
  }) as T;
}
