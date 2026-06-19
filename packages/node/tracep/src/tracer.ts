/**
 * @tracep/sdk – tracer.ts
 *
 * OTel-wrapping Tracer SDK for Node.js.
 *
 * Interface:
 *   const t = new Tracer(endpoint, apiKey, service)
 *   const tid = t.start(name)
 *   t.trace(tid, cls, fn, step, message, { parent?, level? })
 *   await t.end(tid, 'ok' | 'error')
 *   await t.close()   // shutdown provider
 */

import {
  trace,
  context,
  SpanStatusCode,
  type Span,
  type Tracer as OtelTracer,
  type Context,
} from '@opentelemetry/api';
import { NodeTracerProvider, BatchSpanProcessor } from '@opentelemetry/sdk-trace-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { SEMRESATTRS_SERVICE_NAME } from '@opentelemetry/semantic-conventions';

// ---------------------------------------------------------------------------
// Internal types
// ---------------------------------------------------------------------------

/** Key used to deduplicate spans within a single trace. */
type SpanKey = string; // `${cls}::${fn}`

interface TraceEntry {
  /** The root span created by start(). */
  root: Span;
  /** OTel context carrying the root span, used as parent for child spans. */
  rootCtx: Context;
  /** Child spans keyed by cls+fn pair. */
  spans: Map<SpanKey, { span: Span; ctx: Context }>;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function spanKey(cls: string, fn: string): SpanKey {
  return `${cls}::${fn}`;
}

// ---------------------------------------------------------------------------
// Tracer
// ---------------------------------------------------------------------------

export class Tracer {
  private readonly provider: NodeTracerProvider;
  private readonly otelTracer: OtelTracer;
  private readonly traces = new Map<string, TraceEntry>();

  /**
   * @param endpoint  Base URL of the OTLP collector, e.g. "http://localhost:4318"
   * @param apiKey    Bearer token forwarded as Authorization header
   * @param service   Value of the service.name OTel resource attribute
   */
  constructor(
    endpoint: string,
    apiKey: string,
    service: string,
  ) {
    const exporter = new OTLPTraceExporter({
      url: `${endpoint.replace(/\/$/, '')}/v1/traces`,
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
      // Give the exporter up to 10 s before giving up on a single export
      timeoutMillis: 10_000,
    });

    this.provider = new NodeTracerProvider({
      resource: new Resource({
        [SEMRESATTRS_SERVICE_NAME]: service,
      }),
    });

    this.provider.addSpanProcessor(
      new BatchSpanProcessor(exporter, {
        // Buffer up to 50 spans before forcing an export
        maxExportBatchSize: 50,
        // Flush at most once per second
        scheduledDelayMillis: 1_000,
        // Allow up to 512 spans to queue before dropping
        maxQueueSize: 512,
        // Retry budget per export attempt
        exportTimeoutMillis: 10_000,
      })
    );

    this.provider.register();

    this.otelTracer = trace.getTracer(service, '0.1.0');
  }

  // -------------------------------------------------------------------------
  // start()
  // -------------------------------------------------------------------------

  /**
   * Creates a new root span and returns a hex trace-ID string (tid).
   * All subsequent trace()/end() calls use this tid to locate the trace.
   */
  start(name: string): string {
    const root = this.otelTracer.startSpan(name);
    const rootCtx = trace.setSpan(context.active(), root);
    const traceId = root.spanContext().traceId; // 32-char hex

    this.traces.set(traceId, {
      root,
      rootCtx,
      spans: new Map(),
    });

    return traceId;
  }

  // -------------------------------------------------------------------------
  // trace()
  // -------------------------------------------------------------------------

  /**
   * Finds or creates a child span keyed by (cls, fn) and adds a span event.
   *
   * This method is synchronous and non-blocking – spans live in-memory and
   * are flushed asynchronously by the BatchSpanProcessor.
   *
   * @param tid     Trace-ID returned by start()
   * @param cls     Logical class / module name  → code.namespace attribute
   * @param fn      Function / method name       → code.function attribute
   * @param step    Name of the span event
   * @param message Human-readable message added to the event
   * @param opts.parent  tid of a span to use as OTel context parent (optional)
   * @param opts.level   Severity label, e.g. "info" | "warn" | "error"
   */
  trace(
    tid: string,
    cls: string,
    fn: string,
    step: string,
    message: string,
    opts: { parent?: string; level?: string } = {},
  ): void {
    const entry = this.traces.get(tid);
    if (!entry) {
      // Silently drop – never throw from a fire-and-forget tracer
      return;
    }

    const { level = 'info', parent } = opts;
    const key = spanKey(cls, fn);

    // Resolve parent OTel context
    let parentCtx: Context;
    if (parent) {
      // If a parent span-key is provided, look for it in the same trace
      const parentEntry = this.traces.get(parent);
      parentCtx = parentEntry ? parentEntry.rootCtx : entry.rootCtx;
    } else {
      parentCtx = entry.rootCtx;
    }

    // Reuse an existing span for this cls+fn pair, or create a new one
    if (!entry.spans.has(key)) {
      const span = context.with(parentCtx, () =>
        this.otelTracer.startSpan(`${cls}.${fn}`, {
          attributes: {
            'code.namespace': cls,
            'code.function': fn,
          },
        }),
      );
      const spanCtx = trace.setSpan(parentCtx, span);
      entry.spans.set(key, { span, ctx: spanCtx });
    }

    const { span } = entry.spans.get(key)!;

    // Add the event – this is an in-memory operation, never blocks
    span.addEvent(step, {
      message,
      level,
    });
  }

  // -------------------------------------------------------------------------
  // end()
  // -------------------------------------------------------------------------

  /**
   * Sets status on all spans, ends them in reverse creation order, then
   * force-flushes the provider so the batch exporter ships the data.
   *
   * @param tid    Trace-ID returned by start()
   * @param status 'ok' | 'error'
   */
  async end(tid: string, status: 'ok' | 'error'): Promise<void> {
    const entry = this.traces.get(tid);
    if (!entry) return;

    const otelStatus =
      status === 'ok'
        ? { code: SpanStatusCode.OK }
        : { code: SpanStatusCode.ERROR, message: 'trace ended with error' };

    // End child spans first (LIFO)
    const children = [...entry.spans.values()].reverse();
    for (const { span } of children) {
      span.setStatus(otelStatus);
      span.end();
    }

    // End root span
    entry.root.setStatus(otelStatus);
    entry.root.end();

    this.traces.delete(tid);

    // Force-flush is non-blocking from the caller's perspective – the await
    // here only waits for the in-process export to finish, not for a network
    // round-trip to complete (BatchSpanProcessor handles retries internally).
    try {
      await this.provider.forceFlush();
    } catch {
      // Silently drop – never surface exporter errors to callers
    }
  }

  // -------------------------------------------------------------------------
  // close()
  // -------------------------------------------------------------------------

  /**
   * Gracefully shuts down the TracerProvider, flushing all pending spans.
   * Call this once at process exit.
   */
  async close(): Promise<void> {
    // End any still-open traces as errors
    for (const [tid] of this.traces) {
      await this.end(tid, 'error');
    }
    try {
      await this.provider.shutdown();
    } catch {
      // Silently ignore shutdown errors
    }
  }
}
