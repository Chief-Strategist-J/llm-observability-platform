# tracep — Rust OTel Tracer SDK

A fire-and-forget OpenTelemetry tracer SDK that wraps the `opentelemetry` and
`opentelemetry-otlp` crates.  Spans are exported via **OTLP/HTTP JSON** to
your collector with batching (up to 50 spans, flushed every 1 s) and silent
retry on transient failures.

---

## Installation

Add to your `Cargo.toml`:

```toml
[dependencies]
tracep = { path = "packages/rust/tracep" }
tokio  = { version = "1", features = ["full"] }
```

---

## Quick start

```rust
use tracep::Tracer;

#[tokio::main]
async fn main() {
    // 1. Initialise once.
    let tracer = Tracer::new(
        "http://localhost:4318",   // OTLP collector base URL
        "my-secret-api-key",      // Bearer token
        "my-rust-service",        // service.name resource attribute
    ).expect("failed to build tracer");

    // 2. Start a root trace → returns a 32-char hex trace ID.
    let tid = tracer.start("handle-request");

    // 3. Add span events (fire-and-forget, never blocks).
    tracer.trace(
        &tid,
        "AuthService",   // code.namespace (class / module)
        "verify_token",  // code.function
        "token-check",   // span event name (step)
        "token is valid",// message attribute
        None,            // parent span key (None → root)
        Some("info"),    // level attribute
    );

    tracer.trace(
        &tid,
        "DbLayer",
        "fetch_user",
        "db-query",
        "SELECT users WHERE id=42",
        Some("AuthService::verify_token"), // link to parent span
        Some("debug"),
    );

    // 4. End the trace.  Flushes spans in the background.
    tracer.end(&tid, "ok");   // or "error"

    // 5. At process exit — flush remaining spans and shut down.
    tracer.close();
}
```

---

## API reference

| Method | Description |
|--------|-------------|
| `Tracer::new(endpoint, api_key, service)` | Initialise the provider, batch processor, and OTLP exporter. |
| `tracer.start(name) -> String` | Create a root span; return its trace ID as a 32-char hex string (`tid`). |
| `tracer.trace(tid, cls, function, step, message, parent, level)` | Find or create the span for `cls::function`, add a span event named `step`. Unknown `tid` is silently ignored. |
| `tracer.end(tid, status)` | Set status (`"ok"` / `"error"`), end all spans, fire-and-forget flush. Unknown `tid` is silently ignored. |
| `tracer.close()` | Gracefully flush and shut down the OTel provider. Call once at exit. |

---

## Configuration

| Parameter | Default | Notes |
|-----------|---------|-------|
| Batch size | 50 spans | `BatchConfig::max_export_batch_size` |
| Flush interval | 1 second | `BatchConfig::scheduled_delay` |
| Retry attempts | 3 | Exponential back-off starting at 100 ms |
| Export format | OTLP/HTTP JSON | Port `4318`, path `/v1/traces` |
| Auth header | `Authorization: Bearer <api_key>` | Set on every export request |

---

## Running the tests

```bash
cd packages/rust/tracep
cargo test
```

Tests do **not** require a live collector; failed exports are silently dropped.
