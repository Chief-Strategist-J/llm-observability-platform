export interface BaseAdapter {
  [key: string]: any;
}

function getAdapterKeys(adapter: any): string[] {
  const keys = new Set<string>([...Object.keys(adapter)]);
  const proto = Object.getPrototypeOf(adapter);
  if (proto && proto !== Object.prototype) {
    Object.getOwnPropertyNames(proto).forEach((k) => {
      if (k !== "constructor") {
        keys.add(k);
      }
    });
  }
  return Array.from(keys);
}

export function withRetry<T extends BaseAdapter>(adapter: T, retries = 3, delayMs = 300): T {
  const wrapped: any = {};
  const keys = getAdapterKeys(adapter);
  for (const key of keys) {
    const fn = adapter[key];
    if (typeof fn === "function") {
      wrapped[key] = async (...args: any[]) => {
        let attempt = 0;
        while (attempt < retries) {
          try {
            return await fn.call(adapter, ...args);
          } catch (err: any) {
            // Do not retry authorization/authentication failures
            if (err?.status === 401 || err?.status === 403 || err?.code === "UNAUTHORIZED" || err?.code === "TOKEN_EXPIRED") {
              throw err;
            }
            attempt++;
            if (attempt >= retries) throw err;
            await new Promise((r) => setTimeout(r, delayMs * Math.pow(2, attempt - 1)));
          }
        }
      };
    } else {
      wrapped[key] = fn;
    }
  }
  return wrapped as T;
}

export function withCache<T extends BaseAdapter>(adapter: T, ttlMs = 5000): T {
  const cache = new Map<string, { val: any; exp: number }>();
  const wrapped: any = {};
  const keys = getAdapterKeys(adapter);
  for (const key of keys) {
    const fn = adapter[key];
    if (typeof fn === "function" && (key.startsWith("get") || key.startsWith("list") || key.startsWith("fetch"))) {
      wrapped[key] = async (...args: any[]) => {
        const cacheKey = `${key}:${JSON.stringify(args)}`;
        const cached = cache.get(cacheKey);
        if (cached && cached.exp > Date.now()) {
          return cached.val;
        }
        const res = await fn.call(adapter, ...args);
        cache.set(cacheKey, { val: res, exp: Date.now() + ttlMs });
        return res;
      };
    } else {
      wrapped[key] = fn;
    }
  }
  return wrapped as T;
}

export function withCircuitBreaker<T extends BaseAdapter>(adapter: T, threshold = 5, cooldownMs = 10000): T {
  let failures = 0;
  let nextAttemptTime = 0;
  const wrapped: any = {};
  const keys = getAdapterKeys(adapter);

  for (const key of keys) {
    const fn = adapter[key];
    if (typeof fn === "function") {
      wrapped[key] = async (...args: any[]) => {
        if (failures >= threshold && Date.now() < nextAttemptTime) {
          throw new Error(`CircuitBreaker: Call to ${key} blocked due to recent failures.`);
        }
        try {
          const res = await fn.call(adapter, ...args);
          failures = 0;
          return res;
        } catch (err: any) {
          // Do not count 401/403 auth errors towards circuit breaker trips
          if (err?.status !== 401 && err?.status !== 403 && err?.code !== "UNAUTHORIZED" && err?.code !== "TOKEN_EXPIRED") {
            failures++;
            if (failures >= threshold) {
              nextAttemptTime = Date.now() + cooldownMs;
            }
          }
          throw err;
        }
      };
    } else {
      wrapped[key] = fn;
    }
  }
  return wrapped as T;
}
