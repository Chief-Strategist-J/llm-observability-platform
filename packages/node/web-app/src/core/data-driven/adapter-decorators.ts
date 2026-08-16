export interface BaseAdapter {
  [key: string]: (...args: any[]) => Promise<any>;
}

export function withRetry<T extends BaseAdapter>(adapter: T, retries = 3, delayMs = 300): T {
  const wrapped: any = {};
  for (const key of Object.keys(adapter)) {
    const fn = adapter[key];
    if (typeof fn === "function") {
      wrapped[key] = async (...args: any[]) => {
        let attempt = 0;
        while (attempt < retries) {
          try {
            return await fn.call(adapter, ...args);
          } catch (err) {
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
  for (const key of Object.keys(adapter)) {
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

  for (const key of Object.keys(adapter)) {
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
        } catch (err) {
          failures++;
          if (failures >= threshold) {
            nextAttemptTime = Date.now() + cooldownMs;
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
