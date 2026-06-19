# Tracep — Swift OTel Tracing SDK

A thin, fire-and-forget OpenTelemetry tracing wrapper for Swift services.  
Spans are exported via **OTLP/HTTP JSON** to any OTel-compatible collector (Jaeger, Grafana Tempo, Honeycomb, …).

---

## Requirements

| Dependency | Version |
|---|---|
| Swift | ≥ 5.9 |
| opentelemetry-swift | ≥ 1.9.1 |
| macOS | ≥ 12 / Linux (Swift 5.9+) |

---

## Installation

Add the package to your `Package.swift`:

```swift
dependencies: [
    .package(url: "https://github.com/open-telemetry/opentelemetry-swift", from: "1.9.1"),
    .package(path: "../tracep"),   // or a remote URL
],
targets: [
    .target(name: "MyApp", dependencies: [
        "Tracep",
    ]),
]
```

---

## Quick Start

```swift
import Tracep

// 1. Initialise once (e.g. in AppDelegate / main.swift)
let tracer = Tracer(
    endpoint: "http://localhost:4318",   // OTLP collector base URL
    apiKey:   "my-secret-key",          // sent as Authorization: Bearer …
    service:  "order-service"           // service.name resource attribute
)

// 2. Start a root trace — returns an opaque hex trace-ID
let tid = tracer.start(name: "place-order")

// 3. Add events as your code executes
tracer.trace(
    tid:      tid,
    cls:      "OrderController",
    function: "placeOrder",
    step:     "validate",
    message:  "Validating incoming request",
    level:    "info"
)

tracer.trace(
    tid:      tid,
    cls:      "OrderService",
    function: "persist",
    step:     "db-write",
    message:  "Writing order to PostgreSQL",
    parent:   "OrderController.placeOrder",  // optional parent span key
    level:    "debug"
)

// 4. Finish the trace
tracer.end(tid: tid, status: "ok")   // "ok" | "error"

// 5. On shutdown
tracer.close()
```

---

## API Reference

### `Tracer(endpoint:apiKey:service:)`
Bootstraps the OTel pipeline:
- Creates an `OtlpHttpTraceExporter` pointing at `endpoint/v1/traces` on port 4318.
- Sets `Authorization: Bearer <apiKey>` on every request.
- Wraps the exporter in a `BatchSpanProcessor` (buffer 512, flush every 1 s).
- Registers a `TracerProviderSdk` with `service.name = service`.

### `start(name:) -> String`
Creates a root span and returns a **hex trace-ID** you use in every subsequent call.

### `trace(tid:cls:function:step:message:parent:level:)`
Fire-and-forget (runs on a background `DispatchQueue`).  
Finds or creates a child span keyed by `cls.function`, then adds a span event named `step`.

| Parameter | OTel mapping |
|---|---|
| `cls` | `code.namespace` span attribute |
| `function` | `code.function` span attribute |
| `step` | span event name |
| `message` | event attribute `message` |
| `level` | event attribute `level` |
| `parent` | optional parent span key (`"ClassName.methodName"`) |

### `end(tid:status:)`
Ends all spans for `tid` (children first, then root), sets the OTel status to
`.ok` or `.error`, and force-flushes the exporter.

### `close()`
Gracefully shuts down the provider, flushing any in-flight spans.

---

## Internals

| Concern | Mechanism |
|---|---|
| Thread safety | `NSLock` + `Dictionary<String, TraceContext>` |
| Async / non-blocking | `DispatchQueue(label: "com.tracep.background", qos: .background)` |
| Batching | `BatchSpanProcessor` — max 512 spans, flush every 1 s |
| Retry | `RetrySpanExporter` — 3× with exponential back-off, then silent drop |
| Auth | `OtlpConfiguration(headers: [("Authorization", "Bearer …")])` |
| Export format | OTLP/HTTP JSON → `<endpoint>/v1/traces` |

---

## Running Tests

```bash
swift test
```

Tests do **not** require a live collector; network calls are swallowed silently when
no collector is reachable.
