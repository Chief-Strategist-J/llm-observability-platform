/**
 * ALGORITHM & ARCHITECTURE: AsyncLocalStorage Request Context Propagation
 * 
 * Guarantees 100% thread-safe per-async-execution-chain isolation using Node.js native AsyncLocalStorage.
 * Eliminates context-bleeding bugs where concurrent requests on the Node.js event loop could overwrite
 * static mutable context variables and leak cross-tenant data.
 */

import { AsyncLocalStorage } from "async_hooks";
import crypto from "crypto";

export interface RequestContext {
  requestId: string;
  correlationId: string;
  idempotencyKey: string;
  tenantId: string;
  traceparent: string;
  tracestate?: string;
}

export class RequestContextHolder {
  private static asyncLocalStorage = new AsyncLocalStorage<RequestContext>();

  public static generateId(prefix: string): string {
    return `${prefix}-${Date.now()}-${crypto.randomBytes(4).toString('hex')}`;
  }

  public static generateW3CTraceparent(): string {
    const traceId = crypto.randomBytes(16).toString("hex");
    const spanId = crypto.randomBytes(8).toString("hex");
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
    return this.asyncLocalStorage.run(context, callback);
  }

  public static get(): RequestContext {
    const store = this.asyncLocalStorage.getStore();
    if (!store) {
      return this.createDefault();
    }
    return store;
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
