# Master Reference: Write-Once Middleware Engine — HTTP, Kafka, Tracing, Guardrails & Performance
*(Language-agnostic — TypeScript-flavored pseudocode, maps directly to Go, Python, Rust, Java, C++, C#)*

This is the single combined document — the general middleware pattern + guardrails/patterns article and both Kafka articles merged into one, de-duplicated, in reading order: core contract → general guardrails → HTTP layer → tracing → 24 general patterns/edge cases → Kafka guardrails → Kafka pipeline architecture → Kafka producer/consumer middleware (full code) → Kafka performance depth → Kafka edge case catalog → cheat sheets.

---

## PART A — The One Contract Everything Is Built From

A middleware is a function that takes a "next step" and returns a new step wrapping it. HTTP request handling, Kafka publish/consume, tracing, and resilience decorators (retry/cache/circuit-breaker) are all just different `Ctx` shapes plugged into this one contract — written once, in `shared/data-driven/adapter-decorators/`.

```typescript
type Next<Ctx, Result> = (ctx: Ctx) => Promise<Result>;
type Middleware<Ctx, Result> = (next: Next<Ctx, Result>) => Next<Ctx, Result>;

function compose<Ctx, Result>(...middlewares: Middleware<Ctx, Result>[]): Middleware<Ctx, Result> {
  return (final) => middlewares.reduceRight((next, mw) => mw(next), final);
}
```

Everything below is an implementation of this contract for a specific `Ctx`. This function is written once and never touched again by feature code.

---

## PART B — General Guardrails (strict, pass/fail, apply everywhere)

**G1.** Nothing crosses a boundary unvalidated (HTTP in, Kafka message in, DB row out, upstream response in) — every boundary has a named schema-validator call you can point to.

**G2.** Nothing crosses a boundary unserialized through a declared mapper (`fromApi`/`toApi`/`toEvent`/`toRow`) — never manual field-by-field copying.

**G3.** One error taxonomy, one mapper, zero inline `try/catch` translation of errors inside feature code.

**G4.** Every I/O call is wrapped (`withTracing(withCircuitBreaker(withCache(withRetry(adapter))))`), never bare — a raw `db.query()`/`fetch()` inside `service/` or `repository/` is a violation.

**G5.** Folder structure is CI-enforced, not conventional — a linter checks the five-pillar structure (`schema/`, `queries/`, `rules/`, `machines/`, `workflows/`) on every PR.

**G6.** No migration without a rollback file, tested together, in the same PR, before application code depends on the change.

**G7.** Every retryable operation has an idempotency key with a TTL and a real storage backend — never deferred to "later."

**G8.** Every async boundary propagates correlation ID, tenant ID, deadline, and trace context as non-optional context fields.

**G9.** Every consumer has a DLQ, a retry budget, and a poison-message circuit breaker — not launch-optional.

**G10.** Every external-facing schema (OpenAPI/GraphQL/Proto/AsyncAPI) is versioned and immutable once merged — a breaking change is always a new version file.

**G11.** Config and secrets are validated at process boot — fail fast, never fail on first use hours later.

**G12.** No duplicate logic passes review — a duplication scanner (jscpd or equivalent) runs in CI with a hard threshold; this is the guardrail that actually enforces "fewer lines," not a suggestion.

**G13.** Every middleware is tested once, generically, with fault injection — feature tests assert domain behavior only, never re-test generic middleware behavior.

**G14.** Nothing is logged unstructured — no bare `console.log`/`print` in feature code; logging is a middleware, one format, one place it's defined.

**G15.** Graceful shutdown (drain in-flight work on `SIGTERM`) is mandatory for every process holding a Kafka consumer or open connections.

---

## PART C — HTTP / Request Middleware

`Ctx` here is the request context. The pipeline sits in `src/api/rest/v1/router` and wraps every handler before it reaches `service/`.

```typescript
type HttpCtx = {
  request: Request;
  params: Record<string, string>;
  correlationId: string;
  principal?: Principal;
};

const withAuth: Middleware<HttpCtx, Response> = (next) => async (ctx) => {
  const principal = await verifyToken(ctx.request.headers.authorization);
  if (!principal) return unauthorized();
  return next({ ...ctx, principal });
};

const withValidation = (schema: Schema): Middleware<HttpCtx, Response> => (next) => async (ctx) => {
  const result = schema.validate(ctx.request.body);
  if (!result.ok) return badRequest(result.errors);
  return next({ ...ctx, request: { ...ctx.request, body: result.value } });
};

const withRateLimit: Middleware<HttpCtx, Response> = (next) => async (ctx) => {
  if (await isRateLimited(ctx.principal, ctx.request.path)) return tooManyRequests();
  return next(ctx);
};

const withErrorBoundary: Middleware<HttpCtx, Response> = (next) => async (ctx) => {
  try { return await next(ctx); }
  catch (err) { return toErrorResponse(err, ctx.correlationId); } // uses the central mapper, Pattern E2 below
};
```

Feature composition — the pipeline order **is** the declaration:

```typescript
// src/features/auth/index.ts
export const signInHandler = compose(
  withErrorBoundary,
  withTracing("auth.sign_in"),   // Part D
  withRateLimit,
  withValidation(SignInRequestSchema),
  withAuth,                       // omit for public routes
)(authService.signIn);
```

---

## PART D — Tracing (cross-cutting, shared by HTTP and Kafka)

One tracer, one W3C `traceparent`/`tracestate` propagation convention, used identically on both sides so a request → Kafka publish → consume chain stays one contiguous trace graph instead of fragmenting at the queue boundary.

```typescript
const withTracing = (spanName: string): Middleware<HttpCtx, Response> => (next) => async (ctx) => {
  const parentContext = extractW3CTraceContext(ctx.request.headers);
  const span = tracer.startSpan(spanName, { parent: parentContext });
  try {
    const response = await next(ctx);
    span.setAttribute("http.status_code", response.status);
    return response;
  } catch (err) {
    span.recordException(err);
    throw err;
  } finally {
    span.end();
  }
};
```

The Kafka-side equivalent (`withTracingProducer` / `withTracingConsumer`) is in Part I/J — same extract-inject pattern, Kafka message headers instead of HTTP headers.

---

## PART E — 24 General Critical Patterns & Edge Cases

### E1. Error Taxonomy
All errors extend a small closed set declared once in `shared/errors/`: `ValidationError`(400/no-retry), `NotFoundError`(404), `ConflictError`(409), `UnauthorizedError`(401), `ForbiddenError`(403), `RateLimitedError`(429/retry), `UpstreamTimeoutError`(504/retry-with-budget), `UpstreamUnavailableError`(503/circuit-break), `InvariantViolationError`(500, DLQ immediately, no retry). Every error carries `code`, `message`, `retryable: boolean`, `correlationId`.
**Edge case:** third-party SDK errors must be caught and re-wrapped at the adapter boundary — never let a native Postgres/Stripe/AWS error shape leak past it.

### E2. Central Error Mapper
One function, `mapErrorToResponse(err, protocol)`, decides the wire representation (HTTP status, GraphQL extension, gRPC code, Kafka DLQ-or-retry) for every protocol. No feature calls this except the outermost error boundary.
**Edge case:** an error marked `retryable: true` but with an exhausted retry budget must still map to DLQ — the mapper checks budget state, not just the flag.

### E3. Retryable vs Non-Retryable Classification
Classified once, at the error's origin inside the adapter — `withRetry` only ever checks `err.retryable`, never inspects messages/codes itself.
**Edge case:** a write-operation timeout is ambiguous (may have succeeded server-side) — blind retry can double-write; this is why idempotency (G7) is paired with retry, not optional.

### E4. Three-Layer Validation ("do we actually have proper data")
| Layer | Checks | Lives in | Fails as |
|---|---|---|---|
| Boundary/shape | types, required fields, format, ranges | `schema/`, generated from contract | `ValidationError` |
| Domain invariant | business rules needing context | `rules/`, rules engine | `InvariantViolationError` |
| Persistence constraint | uniqueness, FK existence | DB itself, surfaced via adapter | `ConflictError`/`NotFoundError` |
**Edge case:** PATCH requests must distinguish "field absent" from "field explicitly null" or updates silently overwrite data.

### E5. Schema-First Serialization
The contract file is the only place a shape is defined — validation types, mappers, and client SDKs are generated from it, never hand-duplicated.
**Edge case:** optional vs. nullable are different in JSON Schema/GraphQL/Protobuf3 — conflating them causes silent data loss on round-trip.

### E6. Serialization Boundary (fromApi/toApi)
Declarative mapping (`rename`, `pick`, `omit`, `coerce`, `default`) — never imperative field copying.
**Edge case:** circular references passed to a generic serializer without explicit `omit` cause infinite loops; int64/BigInt fields silently lose precision past 2^53 in JSON unless coerced to strings explicitly.

### E7. Versioned Serialization / Schema Evolution
Additive-only within a version; breaking changes always mean a new version running in parallel.
**Edge case:** test forward-compatibility (old consumer reads new message) explicitly — most teams only verify backward-compatibility, which their registry defaults to.

### E8. Idempotency Key Propagation
Every mutating HTTP endpoint accepts `Idempotency-Key`; every Kafka producer call derives a deterministic dedupe key. Dedupe store TTL matches the realistic max retry window.
**Edge case:** the same key reused with a *different* payload must be rejected as `ConflictError`, not silently return the first result.

### E9. Correlation ID Propagation
Generated once at the system's entry edge, threaded through every context, log line, span, and outbound header.
**Edge case:** fan-out (one request → N async jobs) shares the parent correlation ID but each branch gets its own span ID.

### E10. Deadline / Timeout Propagation
An absolute deadline (not a relative duration) is part of every context and propagated downstream.
**Edge case:** retries must subtract already-elapsed time from the remaining budget, or `withRetry(attempts:3, timeoutMs:5000)` can burn 15s against a 3s caller budget.

### E11. Poison Message Handling
Bounded redelivery attempts (retry-count tracked via header, not memory), exponential backoff, then untouched move to `{topic}-dlq` with failure context attached.
**Edge case:** an in-memory retry counter resets on every crash-restart — a poison message that crashes the process retries forever unless the count is externally persisted.

### E12. Consumer Rebalance & Offset Commit
Commit only after successful processing, async/batched, with `onPartitionsRevoked` draining in-flight work first.
**Edge case:** a rebalance mid-batch can cause the same message to be processed by two instances briefly — every handler must be idempotent regardless.

### E13. Backpressure & Bounded Queues
Every internal buffer has an explicit max size and a defined full-behavior (reject or block) — never an unbounded array.
**Edge case:** unbounded `Promise.all()` over a large batch can exhaust a DB pool instantly; chunk with a concurrency limit.

### E14. Circuit Breaker Edge Cases
Scoped per downstream dependency; half-open allows only a small number of probes.
**Edge case:** two endpoints hitting the same dependency must share one breaker instance, or you hide the real aggregate failure rate.

### E15. Graceful Shutdown & Draining
Stop accepting new work on `SIGTERM`, finish in-flight work within a bounded grace period, flush producers, then exit.
**Edge case:** a producer with unflushed buffered messages (`linger.ms` batching) killed mid-batch silently drops them unless `.flush()` is explicitly awaited during shutdown.

### E16. Structured Logging as Middleware
One logging middleware, one structured line per unit of work, tagged with correlation/trace/tenant ID — no bare loggers in feature code.
**Edge case:** logging full request/response bodies by default leaks PII — field-level redaction must be declared per schema.

### E17. Config & Secrets Boundary
Loaded and validated once at boot, immutable typed object passed down — never `process.env` scattered through features.
**Edge case:** a missing optional value silently defaulting wrong (e.g., cache TTL → 0, disabling caching) is worse than a crash — every default is explicit and reviewed.

### E18. Null / Empty / Partial Payload Handling
Nullability declared explicitly per field (`required`/`optional`/`nullable`); defaults applied by the mapper, never inline `??` fallbacks scattered through `service/`.
**Edge case:** a Kafka `null` value is a tombstone on compacted topics — must be special-cased, not treated as a deserialization failure.

### E19. Multi-Tenancy Context Propagation
`tenantId` mandatory on every context, every query (tenant-scoped by construction via the flow-by-flow query pattern), every Kafka header.
**Edge case:** unscoped background jobs must loop per-tenant explicitly — never run one query across all tenants "for efficiency."

### E20. Folder Structure Enforcement (CI-checked)
A structure-validation script fails the build if any of the five pillars is missing or a disallowed folder appears.
**Edge case:** the duplication scanner (G12) is what actually catches copy-paste *within* allowed folders — folder structure alone doesn't prevent it.

### E21. Migration Safety (Expand/Contract + Data-Quality Gates)
Additive-first, verified against production-shaped data, then contracted — the 5-PR column-rename sequence. Every migration PR runs a data-quality check ("what % of rows would fail this new constraint") before merge.
**Edge case:** adding `NOT NULL` to a large table without a default locks it during ALTER in most RDBMSs — add nullable, backfill in batches, then constrain separately.

### E22. Compensating Transactions / Saga
Workflows spanning multiple systems declare an explicit compensating step per side-effecting forward step; the workflow engine runs compensations in reverse order on failure automatically.
**Edge case:** non-compensable steps (e.g., "sent an email") must be ordered last, minimizing what needs manual cleanup on partial failure.

### E23. Testing the Engine Once vs. Features Thin
`shared/*/tests/` gets exhaustive fault-injection tests run once; feature tests assert domain logic only — a feature test asserting "retries 3 times" is testing the wrong layer.
**Edge case:** contract tests must run against generated stubs, not hand-written mocks, or a contract-breaking change can pass tests while breaking real consumers.

### E24. Duplication as a Measured, Enforced Metric
A token-based duplication scanner runs in CI across `service/`, `repository/`, `src/api/` (excluding data-declaration folders, which are expected to look similar) with a hard ceiling.
**Edge case:** a "zero duplication" score achieved by dumping everything into one grab-bag `misc.ts` is a worse outcome — the goal is engine reuse with clear single-responsibility shared modules, not duplication-at-any-cost.

---

## PART F — Naive vs. This Architecture (comparison)

| Concern | Naive (per-feature) | This architecture | Why it compresses code |
|---|---|---|---|
| Error handling | `try/catch` per handler, ad-hoc codes | One taxonomy + one mapper | N×M lines → 1 mapper |
| Validation | Hand-written `if` checks | Schema-declared, 3-layer, generated | Scales with schema files, not code |
| Serialization | Manual object mapping per method | Declarative `fromApi`/`toApi` | Field renames touch one file |
| Retry/cache/breaker | Reimplemented per adapter | Composed decorators, once | New adapter = one line of composition |
| Kafka produce/consume | Raw client calls scattered | Composed middleware pipeline | Idempotence/DLQ/tracing added system-wide via one shared file |
| Tracing | Manual, per-endpoint, inconsistent | One tracer, shared W3C convention | New features get full tracing for free |
| Folder structure | Organic, drifts per developer | CI-enforced five-pillar | Zero ramp-up cost per feature |
| Migrations | Ad-hoc, no rollback discipline | Expand/contract, rollback-paired, data-quality gated | Prevents incidents costlier than any line-count savings |

---

## PART G — Kafka Guardrails (strict, performance-focused)

**K1.** Never block the poll/fetch loop with synchronous CPU-bound work (large-payload decode, encryption) — offload to a worker pool. A blocked poll loop looks like a dead consumer to the broker and triggers a rebalance.

**K2.** Ordering is guaranteed only within a partition, and only if you don't break it yourself. Default: single active worker per partition. Parallelizing within a partition requires a provably idempotent, order-independent handler plus a watermark commit model (Part H.2).

**K3.** Client instances are created once per process, never per call — connection setup (TCP, SASL/TLS, metadata fetch) is expensive.

**K4.** Backpressure is a bounded queue or semaphore, never an unbounded array.

**K5.** Batch size, concurrency limit, and downstream capacity (DB pool, external rate limit) are tuned as one number, not three independent guesses.

**K6.** Every I/O call inside a handler is async/non-blocking — one synchronous call serializes every concurrent unit behind it.

**K7.** GC pause time and event-loop lag are first-class consumer metrics — a pause longer than `session.timeout.ms` is indistinguishable from a crashed consumer.

**K8.** Never fan out a full batch with unbounded concurrency (`Promise.all` over 500 messages, goroutine-per-message with no cap).

**K9.** Decode once, at the boundary, never again downstream.

**K10.** Compression codec is chosen from a benchmark against your actual payload, not a default.

**K11.** Every tunable timeout (`session.timeout.ms`, `max.poll.interval.ms`, `fetch.min.bytes`, `linger.ms`, `batch.size`) is documented with the load-tested reasoning behind its value.

**K12.** Lag, throughput, error rate, and internal queue depth are wired into metrics before shipping — not added reactively after an incident.

**K13.** Offset commits are never on the per-message latency hot path — always async/batched.

**K14.** A throughput regression test runs in CI for any change to the shared middleware pipeline — a regression here degrades every feature silently.

**K15.** No feature sets Kafka client config ad hoc — centralized in `infra/messaging/broker-config`, overrides only through a reviewed table.

**K16.** `max.in.flight.requests.per.connection > 1` with retries enabled can reorder messages unless `enable.idempotence=true` is also set — reviewed together, never toggled independently.

**K17.** Never `sleep()` inside the poll/processing loop for retry backoff — it blocks the partition and can itself exceed `max.poll.interval.ms`, self-triggering the rebalance storm this guardrail exists to prevent. Use retry topics instead (Part J.3).

---

## PART H — The Full Kafka Pipeline Structure (not just middleware)

```
CONSUMER SIDE, top to bottom:
┌─────────────────────────────────────────────────────────────┐
│ 1. BROKER CONNECTION LAYER — one pool/process, boot-time     │  K3
├─────────────────────────────────────────────────────────────┤
│ 2. CONSUMER GROUP COORDINATION — assignment, rebalance,       │  K1,K7
│    heartbeat thread independent of processing thread          │
├─────────────────────────────────────────────────────────────┤
│ 3. FETCHER / PREFETCH BUFFER — per partition, bounded          │  K4
├─────────────────────────────────────────────────────────────┤
│ 4. PARTITIONED WORKER POOL — 1 worker/partition (ordering),   │  K2,K5,K8
│    bounded global concurrency, CPU-bound work offloaded        │  K1
├─────────────────────────────────────────────────────────────┤
│ 5. MIDDLEWARE PIPELINE (Part J)                                │
├─────────────────────────────────────────────────────────────┤
│ 6. OFFSET WATERMARK TRACKER — only if parallelizing per-part.  │
├─────────────────────────────────────────────────────────────┤
│ 7. ASYNC BATCHED COMMITTER — never per-message                 │  K13
└─────────────────────────────────────────────────────────────┘

PRODUCER SIDE:
Application call → Middleware pipeline (Part I) → per-partition
batch accumulator (linger.ms/batch.size) → compression at batch
level (K10) → bounded in-flight requests to broker (K16)
```

### H.1 The Partitioned Worker Pool (the piece almost always skipped)

Wiring the middleware chain directly onto `consumer.on("message", handler)` gives you whatever concurrency model the client library defaults to — usually implicit, usually untested. This stage makes ordering and concurrency an explicit, owned decision.

```typescript
type PartitionKey = `${string}:${number}`; // topic:partition

class PartitionedWorkerPool {
  private queues = new Map<PartitionKey, AsyncQueue<ConsumeCtx>>();
  private globalSemaphore: Semaphore;

  constructor(private opts: { maxGlobalConcurrency: number; onProcess: (ctx: ConsumeCtx) => Promise<void> }) {
    this.globalSemaphore = new Semaphore(opts.maxGlobalConcurrency); // K5, K8
  }

  enqueue(ctx: ConsumeCtx) {
    const key: PartitionKey = `${ctx.topic}:${ctx.partition}`;
    if (!this.queues.has(key)) {
      this.queues.set(key, new AsyncQueue());
      this.drainPartition(key); // exactly one worker loop per partition — K2
    }
    this.queues.get(key)!.push(ctx);
  }

  private async drainPartition(key: PartitionKey) {
    const queue = this.queues.get(key)!;
    for await (const ctx of queue) {
      await this.globalSemaphore.acquire();
      try { await this.opts.onProcess(ctx); }
      finally { this.globalSemaphore.release(); }
      // next iteration only starts after this completes — that IS the ordering guarantee
    }
  }

  async onPartitionRevoked(topic: string, partition: number) {
    const key: PartitionKey = `${topic}:${partition}`;
    const queue = this.queues.get(key);
    if (queue) { await queue.drainAndClose(); this.queues.delete(key); }
  }
}

class Semaphore {
  private available: number;
  private waiters: Array<() => void> = [];
  constructor(private max: number) { this.available = max; }
  async acquire(): Promise<void> {
    if (this.available > 0) { this.available--; return; }
    return new Promise((resolve) => this.waiters.push(resolve));
  }
  release(): void {
    this.available++;
    const next = this.waiters.shift();
    if (next) { this.available--; next(); }
  }
  get inFlight() { return this.max - this.available; } // export as a queue-depth metric — K12
}
```

### H.2 Offset Watermark Tracking (only if K2's default is deliberately relaxed)

```typescript
class OffsetWatermarkTracker {
  private inFlight = new Map<number, Set<string>>();
  private completed = new Map<number, Set<string>>();
  private safeToCommit = new Map<number, string>();

  markStarted(partition: number, offset: string) {
    if (!this.inFlight.has(partition)) this.inFlight.set(partition, new Set());
    this.inFlight.get(partition)!.add(offset);
  }

  markCompleted(partition: number, offset: string) {
    this.inFlight.get(partition)?.delete(offset);
    if (!this.completed.has(partition)) this.completed.set(partition, new Set());
    this.completed.get(partition)!.add(offset);
    this.advanceWatermark(partition);
  }

  private advanceWatermark(partition: number) {
    const completedSet = this.completed.get(partition)!;
    let current = BigInt(this.safeToCommit.get(partition) ?? "-1") + 1n;
    while (completedSet.has(current.toString())) {
      completedSet.delete(current.toString());
      this.safeToCommit.set(partition, current.toString());
      current += 1n;
    }
  }

  getSafeCommitOffset(partition: number): string | undefined {
    return this.safeToCommit.get(partition);
  }
}
```

The async batched committer reads `getSafeCommitOffset` on its interval — never "whatever finished most recently," which would risk losing an earlier still-in-flight message on crash.

---

## PART I — Kafka Producer Middleware (full code)

```typescript
type ProduceCtx<T = unknown> = {
  topic: string; key: string; payload: T;
  headers: Record<string, string>;
  partition?: number; tenantId: string; correlationId: string; deadline: number;
};
```

**withSchemaValidation** — reject before publishing garbage:
```typescript
const withSchemaValidation = (registry: SchemaRegistry): Middleware<ProduceCtx, void> => (next) => async (ctx) => {
  const schema = await registry.getLatest(ctx.topic); // cached, not fetched per call
  const result = schema.validate(ctx.payload);
  if (!result.ok) throw new ValidationError({ code: "SCHEMA_VALIDATION_FAILED", details: result.errors, retryable: false });
  ctx.headers["schema_version"] = String(schema.version);
  return next(ctx);
};
```

**withSerialization** — one codec decision, made once:
```typescript
const withSerialization = (codec: Codec): Middleware<ProduceCtx, void> => (next) => async (ctx) => {
  const serialized = codec.encode(ctx.payload);
  return next({ ...ctx, payload: serialized as any });
};
```

**withIdempotenceGuard** — application-level dedupe, distinct from broker `enable.idempotence`:
```typescript
const withIdempotenceGuard = (dedupeStore: DedupeStore): Middleware<ProduceCtx, void> => (next) => async (ctx) => {
  const dedupeKey = ctx.headers["idempotency_key"] ?? `${ctx.topic}:${ctx.key}:${hash(ctx.payload)}`;
  const acquired = await dedupeStore.setIfAbsent(dedupeKey, ctx.correlationId, { ttlMs: 86_400_000 });
  if (!acquired) { logger.info("duplicate_publish_suppressed", { dedupeKey }); return; }
  try { await next(ctx); }
  catch (err) { await dedupeStore.delete(dedupeKey); throw err; } // release lock so a real retry can succeed
};
```

**withPartitionKeySelection** — avoid hot partitions:
```typescript
const withPartitionKeySelection = (strategy: (ctx: ProduceCtx) => string): Middleware<ProduceCtx, void> =>
  (next) => async (ctx) => {
    const key = strategy(ctx);
    if (!key) throw new InvariantViolationError({ message: `Empty partition key for ${ctx.topic}` });
    return next({ ...ctx, key });
  };

// Compose tenantId + entityId, never a low-cardinality field alone:
const orderEventKeyStrategy = (ctx: ProduceCtx<OrderEvent>) => `${ctx.tenantId}:${ctx.payload.orderId}`;
```

**withTracingProducer** — W3C context injected into Kafka headers:
```typescript
const withTracingProducer: Middleware<ProduceCtx, void> = (next) => async (ctx) => {
  const span = tracer.startSpan(`publish ${ctx.topic}`, {
    kind: SpanKind.PRODUCER,
    attributes: { "messaging.system": "kafka", "messaging.destination": ctx.topic, "messaging.correlation_id": ctx.correlationId },
  });
  injectW3CTraceContext(span, ctx.headers);
  try { await next(ctx); span.setStatus({ code: SpanStatusCode.OK }); }
  catch (err) { span.recordException(err as Error); span.setStatus({ code: SpanStatusCode.ERROR }); throw err; }
  finally { span.end(); }
};
```

**withRetryProducer + withCircuitBreakerProducer** — deadline-aware:
```typescript
const withRetryProducer = (opts: { maxAttempts: number; baseDelayMs: number }): Middleware<ProduceCtx, void> =>
  (next) => async (ctx) => {
    let attempt = 0;
    while (true) {
      const remainingMs = ctx.deadline - Date.now();
      if (remainingMs <= 0) throw new UpstreamTimeoutError({ message: "Deadline exceeded", retryable: false });
      try { return await next(ctx); }
      catch (err) {
        attempt++;
        if (!isRetryable(err) || attempt >= opts.maxAttempts) throw err;
        await sleep(Math.min(opts.baseDelayMs * 2 ** attempt, remainingMs));
      }
    }
  };

const withCircuitBreakerProducer = (breaker: CircuitBreaker): Middleware<ProduceCtx, void> => (next) => async (ctx) => {
  if (breaker.isOpen(ctx.topic)) throw new UpstreamUnavailableError({ message: `Circuit open for ${ctx.topic}`, retryable: true });
  try { const r = await next(ctx); breaker.recordSuccess(ctx.topic); return r; }
  catch (err) { breaker.recordFailure(ctx.topic); throw err; }
};
```

**Full composition:**
```typescript
function buildProducer<T>(topic: string, opts: ProducerOptions) {
  const pipeline = compose<ProduceCtx<T>, void>(
    withTracingProducer,
    withCircuitBreakerProducer(globalBreakerRegistry.for(topic)),
    withRetryProducer({ maxAttempts: 5, baseDelayMs: 100 }),
    withIdempotenceGuard(dedupeStore),
    withSchemaValidation(schemaRegistry),
    withSerialization(opts.codec),
    withPartitionKeySelection(opts.partitionKeyStrategy),
  )(rawKafkaSend);

  return (payload: T, meta: Partial<ProduceCtx>) => pipeline({
    topic, payload, key: "", headers: {}, tenantId: meta.tenantId!,
    correlationId: meta.correlationId ?? generateId(), deadline: meta.deadline ?? Date.now() + 5000,
  });
}

// Feature usage — one line:
export const publishOrderCreated = buildProducer<OrderCreatedEvent>("orders.created.v1", {
  codec: avroCodec, partitionKeyStrategy: orderEventKeyStrategy,
});
```

Order: tracing outermost (captures retries as child spans) → circuit breaker → retry → idempotence/validation/serialization/keying innermost, closest to the actual send.

---

## PART J — Kafka Consumer Middleware (full code)

```typescript
type ConsumeCtx<T = unknown> = {
  topic: string; partition: number; offset: string;
  rawMessage: { key: Buffer | null; value: Buffer | null; headers: Record<string, Buffer>; timestamp: string };
  payload?: T; headers: Record<string, string>;
  tenantId?: string; correlationId?: string; attempt: number;
  heartbeat: () => Promise<void>;
};
```

**withDeserialization** — with tombstone handling:
```typescript
const withDeserialization = (codec: Codec): Middleware<ConsumeCtx, void> => (next) => async (ctx) => {
  if (ctx.rawMessage.value === null) return next({ ...ctx, payload: undefined }); // compacted-topic tombstone
  try { return next({ ...ctx, payload: codec.decode(ctx.rawMessage.value) }); }
  catch (err) {
    throw new ValidationError({ code: "DESERIALIZATION_FAILED", retryable: false, cause: err }); // never retryable
  }
};
```

**withRetryCountHeader** — persisted, crash-safe:
```typescript
const withRetryCountHeader: Middleware<ConsumeCtx, void> = (next) => async (ctx) => {
  const attempt = Number(ctx.rawMessage.headers["x-retry-count"]?.toString() ?? "0");
  return next({ ...ctx, attempt });
};
```
An in-memory counter resets on process restart — a poison message that crashes the consumer every attempt creates an infinite crash-loop unless the count lives in the message header itself.

**withDLQOnFailure** — bounded retries via retry topics, never `sleep()`:
```typescript
const withDLQOnFailure = (opts: { maxAttempts: number; retryTopic: (n: number) => string; dlqTopic: string }):
  Middleware<ConsumeCtx, void> => (next) => async (ctx) => {
  try { await next(ctx); }
  catch (err) {
    if (!(err instanceof AppError)) throw err; // never silently DLQ an unclassified error
    if (!err.retryable || ctx.attempt >= opts.maxAttempts) {
      await produceToDLQ(opts.dlqTopic, {
        originalTopic: ctx.topic, originalPartition: ctx.partition, originalOffset: ctx.offset,
        payload: ctx.rawMessage.value, headers: ctx.headers, failureReason: err.code,
        attemptCount: ctx.attempt, lastFailedAt: new Date().toISOString(),
      });
      return; // DLQ write succeeded — do not crash the loop or block offset commit
    }
    const nextAttempt = ctx.attempt + 1;
    await produceToTopic(opts.retryTopic(nextAttempt), ctx.rawMessage.value, {
      ...ctx.headers, "x-retry-count": String(nextAttempt),
    });
  }
};
```
`sleep()` inside a handler for backoff blocks the whole partition — use separate delayed retry topics instead (K17).

**withTracingConsumer** — extract, don't create orphan traces:
```typescript
const withTracingConsumer: Middleware<ConsumeCtx, void> = (next) => async (ctx) => {
  const parentContext = extractW3CTraceContext(ctx.headers);
  const span = tracer.startSpan(`consume ${ctx.topic}`, {
    kind: SpanKind.CONSUMER, ...(parentContext ? { parent: parentContext } : {}),
    attributes: { "messaging.destination": ctx.topic, "messaging.kafka.partition": ctx.partition, "messaging.retry_count": ctx.attempt },
  });
  try { await next(ctx); span.setStatus({ code: SpanStatusCode.OK }); }
  catch (err) { span.recordException(err as Error); span.setStatus({ code: SpanStatusCode.ERROR }); throw err; }
  finally { span.end(); }
};
```

**withTenantContext** — enforced, not optional:
```typescript
const withTenantContext: Middleware<ConsumeCtx, void> = (next) => async (ctx) => {
  const tenantId = ctx.headers["tenant_id"];
  if (!tenantId) throw new ValidationError({ message: `Missing tenant_id at ${ctx.topic}@${ctx.offset}`, retryable: false });
  return runWithTenantScope(tenantId, () => next({ ...ctx, tenantId }));
};
```

**withConcurrencyLimit** — bounded parallelism (backpressure):
```typescript
const withConcurrencyLimit = (maxConcurrent: number): Middleware<ConsumeCtx, void> => {
  const semaphore = new Semaphore(maxConcurrent);
  return (next) => async (ctx) => {
    await semaphore.acquire();
    try { await next(ctx); } finally { semaphore.release(); }
  };
};
```
Without this, `Promise.all()` over a 500-message poll can open 500 simultaneous DB connections instantly.

**withHeartbeatDuringProcessing** — avoid false rebalances on slow messages:
```typescript
const withHeartbeatDuringProcessing = (intervalMs: number): Middleware<ConsumeCtx, void> => (next) => async (ctx) => {
  const timer = setInterval(() => { ctx.heartbeat().catch(() => {}); }, intervalMs);
  try { return await next(ctx); } finally { clearInterval(timer); }
};
```

**Full composition:**
```typescript
function buildConsumer<T>(topic: string, handler: (payload: T, ctx: ConsumeCtx<T>) => Promise<void>, opts: ConsumerOptions) {
  const pipeline = compose<ConsumeCtx<T>, void>(
    withDLQOnFailure({ maxAttempts: 3, retryTopic: (n) => `${topic}.retry-${n}`, dlqTopic: `${topic}.dlq` }),
    withTracingConsumer,
    withHeartbeatDuringProcessing(10_000),
    withConcurrencyLimit(opts.maxConcurrent ?? 10),
    withTenantContext,
    withRetryCountHeader,
    withDeserialization(opts.codec),
  )(async (ctx) => { if (ctx.payload !== undefined) await handler(ctx.payload, ctx); });

  return { topic, groupId: opts.groupId, onMessage: pipeline };
}

export const userEventsConsumer = buildConsumer<UserCreatedEvent>(
  "users.created.v1",
  (event, ctx) => notificationsProjector.handle(event, ctx.tenantId!),
  { groupId: "notifications-service", codec: avroCodec, maxConcurrent: 20 },
);
```

Order: DLQ-on-failure outermost (catches everything beneath, including deserialization failures) → tracing → heartbeat → concurrency limit → tenant context → retry-count header → deserialization innermost.

**⚠️ Note on stage overlap with Part H.1:** if you also run the `PartitionedWorkerPool`'s global semaphore, pick exactly one layer (the pool's semaphore, or `withConcurrencyLimit`) as the authoritative concurrency cap — running both with different values is a silent, easy-to-miss disagreement.

---

## PART K — Performance & Async Depth

### K.1 Offloading CPU-bound work off the poll thread
```typescript
import { Worker } from "node:worker_threads";

class DecodeWorkerPool {
  private workers: Worker[]; private nextWorker = 0;
  constructor(size: number, workerScript: string) {
    this.workers = Array.from({ length: size }, () => new Worker(workerScript));
  }
  async decode(buf: Buffer, schemaId: number): Promise<unknown> {
    const worker = this.workers[this.nextWorker++ % this.workers.length];
    return new Promise((resolve, reject) => {
      const onMessage = (result: any) => { worker.off("message", onMessage); resolve(result); };
      worker.once("message", onMessage); worker.once("error", reject);
      worker.postMessage({ buf, schemaId }, [buf.buffer]); // transfer, not copy
    });
  }
}
```
Equivalents: Python — `await loop.run_in_executor(pool, decode_fn, raw_bytes)`; Go — bounded worker pool sized to `runtime.NumCPU() - reserved`, never goroutine-per-message; Java/Spring Kafka — offload to a bounded `ExecutorService`, account for dispatch time in `max.poll.interval.ms`; Rust/Tokio — `spawn_blocking`, never `.await` a sync computation on the async runtime's own worker threads.

### K.2 Batching math
A batch flushes when `linger.ms` elapses **or** `batch.size` is reached, whichever first. Tune both together: measure steady-state produce rate, pick `linger.ms` so a batch reaches ~80% of `batch.size` before the timer fires — genuine batching benefit without over-delaying latency-sensitive paths. Re-measure whenever volume changes meaningfully (K11).

### K.3 Prefetch pipelining
`fetch.min.bytes` + `fetch.max.wait.ms` batch the *fetch requests to the broker*, separate from your own processing batching. Too high on low-throughput topics adds latency; too low (default) on high-throughput topics means excess round-trips. Tune per-topic from measured throughput.

### K.4 Concurrency sized against the tightest downstream constraint
```typescript
const dbPoolSize = 20;
const externalApiRateLimit = 50; // req/sec
const safeMargin = 0.7;
const consumerConcurrency = Math.floor(Math.min(dbPoolSize, externalApiRateLimit) * safeMargin); // = 14
```
Every downstream connection pool a handler touches counts, not just the obvious one.

### K.5 Observable backpressure
```typescript
class ObservableBoundedQueue<T> {
  private items: T[] = []; private waiters: Array<() => void> = []; private rejections = 0;
  constructor(private maxSize: number, private metrics: MetricsClient, private name: string) {}
  push(item: T): boolean {
    if (this.items.length >= this.maxSize) {
      this.rejections++; this.metrics.increment(`queue.${this.name}.rejected`); return false;
    }
    this.items.push(item); this.metrics.gauge(`queue.${this.name}.depth`, this.items.length);
    const w = this.waiters.shift(); if (w) w(); return true;
  }
  async pop(): Promise<T> {
    while (this.items.length === 0) await new Promise<void>((r) => this.waiters.push(r));
    const item = this.items.shift()!; this.metrics.gauge(`queue.${this.name}.depth`, this.items.length); return item;
  }
}
```

### K.6 GC pause / event-loop lag tied to rebalance root cause
```typescript
import { monitorEventLoopDelay } from "node:perf_hooks";
const eventLoopMonitor = monitorEventLoopDelay({ resolution: 20 });
eventLoopMonitor.enable();
setInterval(() => {
  const p99Ms = eventLoopMonitor.percentile(99) / 1e6;
  metrics.gauge("consumer.event_loop_lag_p99_ms", p99Ms);
  if (p99Ms > SESSION_TIMEOUT_MS * 0.5) logger.warn("event_loop_lag_approaching_session_timeout", { p99Ms });
}, 5000);
```
JVM equivalent: GC pause time from JMX/`-Xlog:gc` graphed next to consumer lag and rebalance-count — the three together make the root cause visible instead of guessed at.

### K.7 Avoiding redundant serialization round-trips
Decode once → convert via `fromApi` → pass the typed object internally. Anything needing wire format (audit log, outbox) calls the same `toApi`/serializer once, never an ad hoc re-`JSON.stringify` at each call site (K9, E6).

---

## PART L — Kafka Edge Case Catalog (22 total)

**L1. Exactly-once vs. at-least-once.** Kafka transactions give exactly-once *within Kafka*, not against external side effects (charging a card) — those still need application-level idempotency regardless.

**L2. Duplicate delivery on rebalance.** A rebalance between "processed" and "committed" causes reprocessing by the new owner — handlers must be idempotent by design, not by luck.

**L3. Out-of-order messages from bad partition keys.** Order holds only within a partition — key by entity ID (or `tenantId:entityId`), never randomly, for topics where per-entity order matters.

**L4. Large payloads — claim-check pattern.** Don't raise the broker's message-size limit; publish large payloads to blob storage and put only a reference on the Kafka message.

**L5. Compacted topics and tombstones.** A `null` value is a delete signal — must be special-cased in deserialization, not treated as a decode failure.

**L6. Schema registry compatibility direction.** `BACKWARD` compatibility doesn't guarantee `FORWARD` — test both directions explicitly if producers deploy ahead of consumers.

**L7. Consumer lag as a silent failure.** Per-partition lag must be an alerted metric with a threshold — aggregate lag can hide one badly-skewed hot partition.

**L8. Hot partitions from low-cardinality keys.** A single dominant tenant on a shared key bottlenecks that one partition regardless of consumer scaling — composite keys spread load.

**L9. Producer buffer exhaustion.** A slow/unavailable broker can fill the client's send buffer (`max.block.ms` blocking, or a `BufferExhaustedException`) — the circuit breaker should trip on broker error-rate before this, not rely solely on the buffer.

**L10. Idempotent producer config ≠ application idempotency.** `enable.idempotence=true` prevents duplicate delivery from producer network retries only — it does not prevent your application calling `.send()` twice logically. Both `withIdempotenceGuard` and broker idempotence are needed.

**L11. Consumer group ID collisions.** Two unrelated services accidentally sharing a `groupId` silently split the stream between them instead of each getting everything — namespace `groupId` by service.

**L12. Retry-topic ordering loss.** Retried messages lose original ordering relative to the primary topic — an acceptable tradeoff for the failure path, but a conscious one.

**L13. `max.poll.interval.ms` and rebalance storms.** Processing time creeping close to this value causes intermittent rebalances exactly under load — keep heartbeating active or move slow work to an async workflow step.

**L14. Testing without a real cluster.** Unit-test each middleware with a fake `next`/ctx; integration-test the full pipeline via Testcontainers, specifically proving poison messages reach DLQ, commits happen after processing, and a simulated rebalance mid-batch doesn't lose messages.

**L15. Cross-region replication and trace continuity.** Verify `traceparent`/`correlation_id` headers survive MirrorMaker2 (or equivalent) mirroring — a broken trace graph at the DR boundary is worst discovered during an actual failover.

**L16. Header size limits and naming drift.** Headers count toward message size limits; keep one documented header schema (`shared/messaging/topics/header-schema.md`) so features don't fragment naming (`corrId` vs `correlation_id`).

**L17. Rolling-deploy header compatibility.** New required headers or removed old ones during a mixed old/new-consumer deploy window cause intermittent failures — treat header schema changes with the same additive-only discipline as payload schemas (E7).

**L18. Worker pool starvation under a poison-message storm.** Malformed messages hitting a slow failure path (e.g., a timing-out schema-registry lookup) can starve the CPU-offload pool on failing work while healthy messages queue behind — cheap format checks (magic bytes, schema ID presence) should run inline before the expensive offloaded decode.

**L19. Connection pool exhaustion during rebalance bursts.** Every consumer re-establishing assignments can simultaneously spike downstream connection acquisition — size pools and concurrency for rebalance bursts, not just steady state.

**L20. Backpressure with zero error signal.** A block-on-full bounded queue absorbs spikes while lag and latency climb with no error-rate signal — queue depth (K.5) must be alerted independently of error rate.

**L21. Watermark tracker memory growth from a permanently stuck offset.** If one offset keeps cycling retry topics without reaching a terminal DLQ state, the watermark never advances past it and lag grows unbounded even though most messages succeed — every retry path needs a hard `maxAttempts` terminating in DLQ.

**L22. Compression CPU cost outweighing its own savings.** At high produce volume on CPU-constrained producers, zstd's better ratio can cost more CPU than the network savings are worth — benchmark against your actual payload and instance sizing (K10), don't copy a "zstd is best practice" rule blindly.

---

## PART M — Composition Cheat Sheets

```
HTTP (outside → in):
  withErrorBoundary → withTracing → withRateLimit → withValidation → withAuth → handler

KAFKA PRODUCER (outside → in):
  withTracingProducer → withCircuitBreakerProducer → withRetryProducer →
  withIdempotenceGuard → withSchemaValidation → withSerialization →
  withPartitionKeySelection → raw send()

KAFKA CONSUMER (outside → in):
  withDLQOnFailure (outermost — must catch everything below)
  → withTracingConsumer → withHeartbeatDuringProcessing → withConcurrencyLimit
  → withTenantContext → withRetryCountHeader → withDeserialization → domain handler

KAFKA FULL PIPELINE (structural layers, not just middleware):
  Broker connection pool → Consumer group coordination → Prefetch buffer →
  Partitioned worker pool (ordering + global concurrency cap) →
  [Middleware chain above] → Offset watermark tracker (if parallel-per-partition) →
  Async batched committer
```

Deviating from these orders is where subtle bugs hide — e.g., `withDLQOnFailure` anywhere but outermost lets a tracing or deserialization error bypass the DLQ path and crash the consumer loop instead.