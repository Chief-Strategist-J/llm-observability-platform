# tracep

> Fire-and-forget OpenTelemetry tracer SDK for Python.

## Install

```bash
pip install .
# or for development
pip install -e ".[dev]"
```

## Quick start

```python
from tracep import Tracer

# 1 — create a tracer (once, at application startup)
tracer = Tracer("http://localhost:4318", "my-api-key", "my-service")

# 2 — start a root trace → returns a hex trace-ID string
tid = tracer.start("payment-flow")

# 3 — record events (non-blocking, background queue)
tracer.trace(tid, "PaymentService", "charge", "validate", "card validated ok")
tracer.trace(tid, "PaymentService", "charge", "submit",   "charge submitted",
             parent="PaymentService/charge", level="info")

# 4 — end the trace ("ok" | "error")
tracer.end(tid, "ok")

# 5 — shutdown gracefully (optional, call at process exit)
tracer.close()
```

## API

| Method | Description |
|--------|-------------|
| `Tracer(endpoint, api_key, service)` | Initialise the tracer. `endpoint` is the base OTLP collector URL (e.g. `http://localhost:4318`). |
| `start(name) -> str` | Begin a new root trace. Returns a 32-char hex trace ID (*tid*). |
| `trace(tid, cls, function, step, message, *, parent=None, level="info")` | Record a step inside a trace. Fire-and-forget. |
| `end(tid, status)` | Finish the trace. `status` must be `"ok"` or `"error"`. Force-flushes the exporter. |
| `close()` | Graceful shutdown (joins background thread, shuts down provider). |

## Internals

- **Transport** — OTLP/HTTP JSON, port 4318, path `/v1/traces`.
- **Auth** — `Authorization: Bearer <api_key>` header on every request.
- **Batching** — `BatchSpanProcessor` with `max_export_batch_size=50`, `schedule_delay=1 s`.
- **Retry** — OTel SDK default: 3 attempts with 100 ms / 200 ms / 400 ms exponential back-off.
- **Non-blocking** — `trace()` and `end()` enqueue work onto a daemon `queue.Queue`; the caller never blocks.
