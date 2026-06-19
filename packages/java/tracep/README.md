# tracep-sdk — Java

> Fire-and-forget OTel-backed tracing SDK.  
> Wraps the OpenTelemetry Java SDK and exports spans via OTLP/HTTP JSON.

## Requirements

| Tool | Version |
|------|---------|
| Java | 17 +    |
| Maven | 3.8 +  |

---

## Quick start

### 1. Add the dependency (after `mvn install`)

```xml
<dependency>
  <groupId>io.tracep</groupId>
  <artifactId>tracep-sdk</artifactId>
  <version>0.1.0</version>
</dependency>
```

### 2. Use the SDK

```java
import io.tracep.Tracer;

public class Main {
    public static void main(String[] args) throws Exception {

        // Initialise once – endpoint, api-key, service name
        try (Tracer tracer = new Tracer(
                "http://localhost:4318",   // OTLP collector base URL
                "my-secret-api-key",       // Bearer token
                "order-service"            // service.name
        )) {

            // Open a root trace – returns a 32-char hex trace ID
            String tid = tracer.start("process-order");

            // Record events (fire-and-forget, never blocks)
            tracer.trace(tid, "OrderService", "validate",
                    "validation-start", "Validating order #42");

            tracer.trace(tid, "OrderService", "validate",
                    "validation-end", "Order #42 is valid");

            tracer.trace(tid, "PaymentService", "charge",
                    "charge-attempt", "Charging card ****1234",
                    null,             // parent span-id (optional)
                    "info"            // level: info | warn | error
            );

            // Close the trace with a final status
            tracer.end(tid, "ok");    // "ok" | "error"

            // tracer.close() is called automatically by try-with-resources
        }
    }
}
```

---

## Advanced configuration (TracerOptions builder)

```java
import io.tracep.Tracer;
import io.tracep.TracerOptions;
import java.time.Duration;

TracerOptions opts = TracerOptions.builder()
        .endpoint("http://otel-collector:4318")
        .apiKey("secret")
        .service("checkout-service")
        .maxExportBatchSize(50)           // buffer up to 50 spans (default)
        .scheduleDelay(Duration.ofSeconds(1)) // flush every 1 s (default)
        .maxRetries(3)                    // retry count hint (default)
        .build();

Tracer tracer = new Tracer(opts);
```

---

## API reference

| Method | Description |
|--------|-------------|
| `Tracer(endpoint, apiKey, service)` | Construct with defaults |
| `Tracer(TracerOptions)` | Construct with full options |
| `String start(name)` | Open a root trace → returns 32-char hex trace ID |
| `void trace(tid, cls, function, step, message)` | Add event (level=info, no parent) |
| `void trace(tid, cls, function, step, message, parent, level)` | Add event with optional parent span-id and level |
| `void end(tid, status)` | Close trace; status = `"ok"` \| `"error"` |
| `void close()` | Flush & shut down; implements `AutoCloseable` |

---

## Building

```bash
# compile + run tests
mvn test

# package (produces tracep-sdk-0.1.0.jar + tracep-sdk-0.1.0-all.jar)
mvn package
```

---

## Internals

| Concern | Implementation |
|---------|---------------|
| Export | `OtlpHttpSpanExporter` → `<endpoint>/v1/traces` port 4318 |
| Auth | `Authorization: Bearer <apiKey>` header |
| Batching | `BatchSpanProcessor` – 50 spans / 1 s |
| Retry | OTel SDK built-in exponential back-off (3 attempts) |
| Async | Single daemon `ExecutorService` – callers never block |
| State | `ConcurrentHashMap<tid, TraceContext>` |
| Span reuse | Same `class+function` key reuses one child span across `trace()` calls |
