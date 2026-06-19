# tracep – Dart OpenTelemetry Tracing SDK

A lightweight, fire-and-forget OpenTelemetry tracing SDK for Dart that wraps
`package:opentelemetry` with a clean, consistent interface.

## Features

- **OTel-native**: Uses `package:opentelemetry` TracerProvider, BatchSpanProcessor, OTLP/HTTP JSON export
- **Fire-and-forget**: All operations enqueue on an internal `Stream` queue — callers never block
- **Batched export**: Buffer up to 50 spans, flush every 1 second
- **Retry with back-off**: 3 attempts (200 ms → 400 ms → 800 ms), then silent drop
- **Auth header**: `Authorization: Bearer <api_key>` set on the OTLP exporter
- **Thread-safe**: Internal state protected by `package:synchronized` `Lock`

## Installation

Add to your `pubspec.yaml`:

```yaml
dependencies:
  tracep:
    path: packages/dart/tracep   # or the published package name
```

## Quick Start

```dart
import 'package:tracep/tracep.dart';

Future<void> main() async {
  // 1. Create and initialise once.
  final tracer = Tracer(
    endpoint: 'http://otel-collector:4318',
    apiKey: 'my-secret-key',
    service: 'payment-service',
  );
  await tracer.init();

  // 2. Start a root trace – returns a 32-char hex trace-id immediately.
  final tid = tracer.start('process-payment');

  // 3. Add span events (fire-and-forget, never blocks).
  tracer.trace(
    tid,
    'PaymentController',  // class  → code.namespace attribute
    'charge',             // method → code.function attribute
    'validate',           // step   → OTel span event name
    'Validating card',    // message attribute on the event
    level: 'info',
  );

  tracer.trace(
    tid,
    'StripeGateway',
    'authorise',
    'api-call',
    'Calling Stripe API',
    parent: 'PaymentController|charge',  // links to parent span
    level: 'info',
  );

  // 4. End the trace – awaitable, ensures flush before returning.
  await tracer.end(tid, 'ok');   // status: 'ok' | 'error'

  // 5. Shutdown on application exit.
  await tracer.close();
}
```

## API Reference

### `Tracer({required String endpoint, required String apiKey, required String service})`

Creates a tracer instance. No OTel objects are created until `init()` is called.

| Parameter  | Description                                   |
|------------|-----------------------------------------------|
| `endpoint` | OTLP collector base URL (e.g. `http://host:4318`) |
| `apiKey`   | Bearer token sent in `Authorization` header   |
| `service`  | Value for the `service.name` OTel resource    |

### `Future<void> init()`

Initialises the `TracerProvider`, `BatchSpanProcessor`, and internal async queue.
Must be called once before any other method. Subsequent calls are no-ops.

### `String start(String name)`

Creates a new root OTel span named `name`.  
Returns the **trace-id** as a 32-character lower-hex string (`tid`).

### `void trace(String tid, String cls, String function, String step, String message, {String? parent, String level = 'info'})`

Adds an event to the span identified by `cls`+`function` under trace `tid`.
The span is created on first call and reused on subsequent calls with the same
`cls`+`function` pair.

| Parameter  | OTel mapping                                    |
|------------|-------------------------------------------------|
| `cls`      | `code.namespace` span attribute                 |
| `function` | `code.function` span attribute                  |
| `step`     | Span event name                                 |
| `message`  | `message` attribute on the span event           |
| `level`    | `level` attribute on the span event             |
| `parent`   | Optional `"cls\|function"` key of parent span   |

Silently ignored when `tid` is unknown (e.g. after `end()`).

### `Future<void> end(String tid, String status)`

Ends all spans for `tid`, sets OTel status (`ok` → `StatusCode.ok`,
`error` → `StatusCode.error`), and force-flushes the exporter.

### `Future<void> close()`

Gracefully shuts down the provider. Ends any still-open traces with `ok` status.

## Running Tests

```bash
cd packages/dart/tracep
dart pub get
dart test
```

## OTel Collector Config Example

```yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318

exporters:
  logging:
    loglevel: debug

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [logging]
```
