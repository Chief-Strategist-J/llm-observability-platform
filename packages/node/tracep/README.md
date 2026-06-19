# @tracep/sdk — Node.js Tracer SDK

Fire-and-forget OpenTelemetry tracing SDK for Node.js.  
Wraps `@opentelemetry/sdk-node` + `@opentelemetry/exporter-trace-otlp-http`.

## Install

```bash
npm install @tracep/sdk
```

## Quick start

```typescript
import { Tracer } from '@tracep/sdk';

// Initialise once at application start
const tracer = new Tracer(
  'http://otel-collector:4318', // OTLP/HTTP collector base URL
  'my-secret-api-key',          // Bearer token (sent as Authorization header)
  'my-service',                 // service.name OTel resource attribute
);

// --- Start a root trace (returns a hex trace-ID string) ---
const tid = tracer.start('checkout-flow');

// --- Add events to named spans (fire-and-forget, never blocks) ---
tracer.trace(tid, 'OrderService', 'validateCart',  'validate',  'Cart validated');
tracer.trace(tid, 'OrderService', 'chargeCard',    'charge',    'Card charged',  { level: 'info' });
tracer.trace(tid, 'EmailService', 'sendReceipt',   'email-sent','Receipt queued', { level: 'info' });

// --- Finish the trace (flushes the batch exporter) ---
await tracer.end(tid, 'ok');   // or 'error'

// --- Shutdown at process exit ---
await tracer.close();
```

## API

### `new Tracer(endpoint, apiKey, service)`

| Parameter  | Type     | Description |
|------------|----------|-------------|
| `endpoint` | `string` | Base URL of the OTLP/HTTP collector, e.g. `http://localhost:4318` |
| `apiKey`   | `string` | Bearer token sent in the `Authorization` header |
| `service`  | `string` | OTel `service.name` resource attribute |

### `tracer.start(name): string`

Creates a new root span and returns a **trace-ID** (`tid`) hex string.  
Pass this `tid` to all subsequent `trace()` and `end()` calls.

### `tracer.trace(tid, cls, fn, step, message, opts?): void`

Adds an event to the span identified by `(cls, fn)` within trace `tid`.  
The span is created lazily on first call and **reused** on subsequent calls with the same `(cls, fn)` pair.

| Parameter | Type | Description |
|-----------|------|-------------|
| `tid` | `string` | Trace-ID from `start()` |
| `cls` | `string` | Class / module name → sets `code.namespace` attribute |
| `fn` | `string` | Function / method name → sets `code.function` attribute |
| `step` | `string` | Span event name |
| `message` | `string` | Human-readable message added to the event |
| `opts.parent` | `string?` | Trace-ID to use as OTel context parent |
| `opts.level` | `string?` | Severity label (default `"info"`) |

> **Fire-and-forget** — spans are in-memory; the `BatchSpanProcessor` ships them to the collector asynchronously (max 50 per batch, flush every 1 s).

### `tracer.end(tid, status): Promise<void>`

Sets the status on all spans, ends them, then calls `provider.forceFlush()`.

| Value | OTel mapping |
|-------|-------------|
| `'ok'` | `SpanStatusCode.OK` |
| `'error'` | `SpanStatusCode.ERROR` |

### `tracer.close(): Promise<void>`

Ends all open traces as `'error'`, then calls `provider.shutdown()`.  
Call this **once** at process exit (`SIGTERM`, `beforeExit`, etc.).

## OTel internals

| Setting | Value |
|---------|-------|
| Exporter | OTLP/HTTP JSON |
| Export URL | `{endpoint}/v1/traces` |
| Auth | `Authorization: Bearer <apiKey>` |
| Batch size | 50 spans |
| Flush interval | 1 000 ms |
| Export timeout | 10 000 ms |
| Max queue | 512 spans |
| On failure | Silent drop (never throws) |

## Development

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Run unit tests
npm test

# Type-check without emitting
npm run lint
```

## Process exit hook (recommended)

```typescript
process.on('SIGTERM', async () => {
  await tracer.close();
  process.exit(0);
});
```
