# tracep — Kotlin SDK

> Fire-and-forget OpenTelemetry tracing SDK for Kotlin services.

## Installation

Add to your `build.gradle.kts`:

```kotlin
dependencies {
    implementation("io.tracep:tracep:0.1.0")
}
```

Or build locally:

```bash
cd packages/kotlin/tracep
./gradlew build
```

## Quick Start

```kotlin
import io.tracep.Tracer
import io.tracep.parentKey

fun main() {
    // 1. Initialise once (usually at app startup)
    val tracer = Tracer(
        endpoint = "https://otel.example.com",   // OTLP/HTTP endpoint (port 4318)
        apiKey   = "my-api-key",
        service  = "checkout-service",
    )

    // 2. Start a root trace — returns a 32-char hex trace-id
    val tid = tracer.start("checkout-flow")

    // 3. Record step events — fire and forget, never blocks
    tracer.trace(
        tid      = tid,
        cls      = "CartService",
        function = "validateCart",
        step     = "cart.validated",
        message  = "Cart #42 passed validation",
        level    = "info",
    )

    // 4. Nest spans with the parent parameter
    val cartKey = parentKey("CartService", "validateCart")

    tracer.trace(
        tid      = tid,
        cls      = "PaymentService",
        function = "charge",
        step     = "payment.charged",
        message  = "Charged \$99.00 to card ****1234",
        parent   = cartKey,     // links to CartService#validateCart span
        level    = "info",
    )

    // 5. End the trace — "ok" | "error"
    tracer.end(tid, "ok")

    // 6. Shutdown — flush and release resources (call on app exit)
    tracer.close()
}
```

### Reading the API key from the environment

```kotlin
val tracer = Tracer.fromEnv(
    endpoint = "https://otel.example.com",
    service  = "my-service",
    // apiKey defaults to env var TRACEP_API_KEY
)
```

## API Reference

| Method | Returns | Description |
|--------|---------|-------------|
| `Tracer(endpoint, apiKey, service)` | `Tracer` | Create a new tracer instance. |
| `Tracer.fromEnv(endpoint, service)` | `Tracer` | Factory that reads `TRACEP_API_KEY` from env. |
| `start(name)` | `String` | Start a root trace; returns 32-char hex trace-id. |
| `trace(tid, cls, function, step, message, parent?, level?)` | `Unit` | Record a step event (fire-and-forget). |
| `end(tid, status)` | `Unit` | End all spans; `status` = `"ok"` or `"error"`. |
| `close()` | `Unit` | Flush exporter and shut down. |
| `parentKey(cls, function)` | `String` | Build a parent-span key for `trace(parent=…)`. |

## Internals

| Concern | Implementation |
|---------|----------------|
| Export protocol | OTLP/HTTP JSON → `<endpoint>/v1/traces` |
| Authentication | `Authorization: Bearer <apiKey>` header |
| Buffering | `BatchSpanProcessor` — 50 spans per batch |
| Flush interval | 1 second |
| Retry | OTel SDK built-in — 3× exponential back-off, then drop |
| Concurrency | `CoroutineScope(Dispatchers.IO + SupervisorJob())` |
| Span reuse | One span per `class+function` pair per trace |

## Running Tests

```bash
cd packages/kotlin/tracep
./gradlew test
```

Test output is written to `build/reports/tests/test/index.html`.
