import { RULES_ENGINE_CONSTANTS } from "../rules-engine/constants";
import { errorRegistry } from "../rules-engine/error-registry";

export interface RequestContext {
  requestId: string;
  correlationId: string;
  idempotencyKey: string;
  tenantId: string;
  traceparent: string;
  tracestate?: string;
}

interface StorageAdapter<T> {
  run<R>(store: T, callback: () => R): R;
  getStore(): T | undefined;
}

class InMemoryStorageAdapter<T> implements StorageAdapter<T> {
  private currentStore: T | undefined;

  public run<R>(store: T, callback: () => R): R {
    const prev = this.currentStore;
    this.currentStore = store;
    try {
      return callback();
    } finally {
      this.currentStore = prev;
    }
  }

  public getStore(): T | undefined {
    return this.currentStore;
  }
}

function initAsyncLocalStorage<T>(): StorageAdapter<T> {
  try {
    const g = globalThis as any;
    if (typeof g.AsyncLocalStorage === "function") {
      return new g.AsyncLocalStorage();
    }
  } catch (err: any) {
    const errDesc = errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_CONTEXT_STORAGE_INIT_FAILED);
    if (typeof console !== "undefined" && console.warn) {
      console.warn(`${errDesc.message}: ${err?.message || String(err)}`);
    }
  }
  return new InMemoryStorageAdapter<T>();
}

function getRandomHex(bytes: number): string {
  if (typeof globalThis !== "undefined" && globalThis.crypto && typeof globalThis.crypto.getRandomValues === "function") {
    const arr = new Uint8Array(bytes);
    globalThis.crypto.getRandomValues(arr);
    return Array.from(arr, (b) => b.toString(16).padStart(2, "0")).join("");
  }
  return Array.from({ length: bytes * 2 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
}

export class RequestContextHolder {
  private static storage: StorageAdapter<RequestContext> = initAsyncLocalStorage<RequestContext>();

  public static generateId(prefix: string): string {
    return `${prefix}-${Date.now()}-${getRandomHex(4)}`;
  }

  public static generateW3CTraceparent(): string {
    const traceId = getRandomHex(16);
    const spanId = getRandomHex(8);
    return `00-${traceId}-${spanId}-01`;
  }

  public static create(incoming?: Partial<RequestContext>): RequestContext {
    const requestId = incoming?.requestId || this.generateId('req');
    const correlationId = incoming?.correlationId || this.generateId('corr');
    const idempotencyKey = incoming?.idempotencyKey || incoming?.requestId || this.generateId('idem');
    const traceparent = incoming?.traceparent || this.generateW3CTraceparent();

    return {
      requestId,
      correlationId,
      idempotencyKey,
      tenantId: incoming?.tenantId || 'tenant-default',
      traceparent,
      tracestate: incoming?.tracestate || 'rojo=1',
    };
  }

  public static run<T>(context: RequestContext, callback: () => T): T {
    return this.storage.run(context, callback);
  }

  public static get(): RequestContext {
    try {
      const store = this.storage.getStore();
      if (!store) {
        return this.createDefault();
      }
      return store;
    } catch (err: any) {
      const errDesc = errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_UNKNOWN);
      if (typeof console !== "undefined" && console.error) {
        console.error(`${errDesc.message}: ${err?.message || String(err)}`);
      }
      return this.createDefault();
    }
  }

  private static createDefault(): RequestContext {
    return {
      requestId: this.generateId('req'),
      correlationId: this.generateId('corr'),
      idempotencyKey: this.generateId('idem'),
      tenantId: 'tenant-default',
      traceparent: this.generateW3CTraceparent(),
      tracestate: 'rojo=1',
    };
  }
}
