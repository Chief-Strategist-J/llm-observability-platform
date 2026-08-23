export interface RequestContext {
  requestId: string;
  correlationId: string;
  idempotencyKey: string;
  tenantId?: string;
  traceparent: string;
  tracestate?: string;
}

export class RequestContextHolder {
  private static activeContext: RequestContext | null = null;

  public static generateId(prefix: string): string {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
  }

  public static generateW3CTraceparent(): string {
    const hexChars = '0123456789abcdef';
    let traceId = '';
    let spanId = '';
    for (let i = 0; i < 32; i++) traceId += hexChars[Math.floor(Math.random() * 16)];
    for (let i = 0; i < 16; i++) spanId += hexChars[Math.floor(Math.random() * 16)];
    return `00-${traceId}-${spanId}-01`;
  }

  public static create(incoming?: Partial<RequestContext>): RequestContext {
    const requestId = incoming?.requestId || this.generateId('req');
    const correlationId = incoming?.correlationId || this.generateId('corr');
    const idempotencyKey = incoming?.idempotencyKey || incoming?.requestId || this.generateId('idem');
    const traceparent = incoming?.traceparent || this.generateW3CTraceparent();

    const ctx: RequestContext = {
      requestId,
      correlationId,
      idempotencyKey,
      tenantId: incoming?.tenantId || 'tenant-default',
      traceparent,
      tracestate: incoming?.tracestate || 'rojo=1',
    };

    this.activeContext = ctx;
    return ctx;
  }

  public static get(): RequestContext {
    if (!this.activeContext) {
      return this.create();
    }
    return this.activeContext;
  }

  public static set(ctx: RequestContext): void {
    this.activeContext = ctx;
  }

  public static clear(): void {
    this.activeContext = null;
  }
}
