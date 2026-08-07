import type { CrudPort } from './create-entity-adapter';

export interface DecoratorOptions {
  retries?: number;
  backoffMs?: number;
  ttlMs?: number;
  failureThreshold?: number;
  resetTimeoutMs?: number;
}

export function withRetry<T>(port: CrudPort<T>, options: DecoratorOptions = {}): CrudPort<T> {
  const maxRetries = options.retries ?? 3;
  const backoff = options.backoffMs ?? 300;

  async function retryOperation<R>(fn: () => Promise<R>): Promise<R> {
    let lastError: unknown;
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (err) {
        lastError = err;
        if (attempt < maxRetries) {
          await new Promise((res) => setTimeout(res, backoff * Math.pow(2, attempt)));
        }
      }
    }
    throw lastError;
  }

  return {
    list: () => retryOperation(() => port.list()),
    get: (id) => retryOperation(() => port.get(id)),
    create: (payload) => retryOperation(() => port.create(payload)),
    update: (id, payload) => retryOperation(() => port.update(id, payload)),
    remove: (id) => retryOperation(() => port.remove(id)),
  };
}

export function withCache<T>(port: CrudPort<T>, options: DecoratorOptions = {}): CrudPort<T> {
  const ttl = options.ttlMs ?? 60000;
  const cache = new Map<string, { data: unknown; timestamp: number }>();

  function getCached<R>(key: string, fetchFn: () => Promise<R>): Promise<R> {
    const entry = cache.get(key);
    const now = Date.now();
    if (entry && now - entry.timestamp < ttl) {
      return Promise.resolve(entry.data as R);
    }
    return fetchFn().then((data) => {
      cache.set(key, { data, timestamp: now });
      return data;
    });
  }

  function invalidateCache() {
    cache.clear();
  }

  return {
    list: () => getCached('list', () => port.list()),
    get: (id) => getCached(`get:${id}`, () => port.get(id)),
    create: async (payload) => {
      const res = await port.create(payload);
      invalidateCache();
      return res;
    },
    update: async (id, payload) => {
      const res = await port.update(id, payload);
      invalidateCache();
      return res;
    },
    remove: async (id) => {
      await port.remove(id);
      invalidateCache();
    },
  };
}

export function withCircuitBreaker<T>(port: CrudPort<T>, options: DecoratorOptions = {}): CrudPort<T> {
  const threshold = options.failureThreshold ?? 5;
  const resetTimeout = options.resetTimeoutMs ?? 30000;

  let failures = 0;
  let state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
  let nextAttempt = 0;

  async function execute<R>(fn: () => Promise<R>): Promise<R> {
    const now = Date.now();
    if (state === 'OPEN') {
      if (now > nextAttempt) {
        state = 'HALF_OPEN';
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await fn();
      if (state === 'HALF_OPEN') {
        state = 'CLOSED';
        failures = 0;
      }
      return result;
    } catch (err) {
      failures++;
      if (failures >= threshold) {
        state = 'OPEN';
        nextAttempt = Date.now() + resetTimeout;
      }
      throw err;
    }
  }

  return {
    list: () => execute(() => port.list()),
    get: (id) => execute(() => port.get(id)),
    create: (payload) => execute(() => port.create(payload)),
    update: (id, payload) => execute(() => port.update(id, payload)),
    remove: (id) => execute(() => port.remove(id)),
  };
}

export function withTracing<T>(port: CrudPort<T>, name: string): CrudPort<T> {
  async function trace<R>(op: string, fn: () => Promise<R>): Promise<R> {
    try {
      return await fn();
    } catch (err) {
      throw err;
    }
  }

  return {
    list: () => trace(`${name}.list`, () => port.list()),
    get: (id) => trace(`${name}.get`, () => port.get(id)),
    create: (payload) => trace(`${name}.create`, () => port.create(payload)),
    update: (id, payload) => trace(`${name}.update`, () => port.update(id, payload)),
    remove: (id) => trace(`${name}.remove`, () => port.remove(id)),
  };
}
