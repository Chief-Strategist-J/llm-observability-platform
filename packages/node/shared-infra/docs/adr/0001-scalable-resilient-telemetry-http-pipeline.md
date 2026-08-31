# ADR 0001: Pure Functional Resilient HTTP Client Pipeline with Full OpenTelemetry Decision & Code Telemetry

* **Status**: Accepted
* **Deciders**: Architecture Team, Core Infrastructure Working Group
* **Date**: 2026-08-31
* **Scope**: `@observability/shared-infra` (`packages/node/shared-infra`)

---

## 1. Context and Problem Statement

The LLM Observability Platform processes high volumes of distributed RPCs, telemetry query feeds, and real-time LLM cost/quality data across microservices. The existing network layer suffered from:
1. **Thundering Herd Effects**: Concurrent duplicate read requests sent identical queries to downstream servers.
2. **Caller UI Crashes**: Traditional `AbortController` cancellation rejected pending promises with `AbortError`, causing UI component crashes.
3. **Black-box Observability**: Developers could not trace which component line number initiated an HTTP request or why a specific cache/circuit breaker decision was made.
4. **Contract-Fragile If/Else & Loop Imperative Spaghetti**: Mutable state loops made retry jitter and header propagation difficult to audit.

We need a standardized, resilient, pure functional HTTP client pipeline with deep OpenTelemetry decision and code-location telemetry.

---

## 2. Decision Drivers

* **Pure Functional Architecture**: Zero `if` statements and zero `for/while` loops. Pipeline execution must be composed using `.reduce()`, `.map()`, and pure ternary expressions.
* **Zero Hardcoded Strings**: All HTTP verbs, headers, status codes, tracer names, and span event keys must be enforced via `as const` constant objects (`HTTP_CONSTANTS`, `RULES_ENGINE_CONSTANTS`).
* **Singleflight Request Collapsing**: Duplicate concurrent read requests must map to a single in-flight `Promise`, returning data to all callers simultaneously without throwing `AbortError`.
* **Idempotency Key Preservation**: The `x-idempotency-key` header must be generated once per logical operation and preserved identically across all retry attempts.
* **Header & Endpoint Driven Caching**: Cache lookup must be dynamically bypassed when `noCache: true` or `Cache-Control: no-cache, no-store` headers are present.
* **Comprehensive OpenTelemetry Telemetry**: Spans must record caller location (`code.function`, `code.filepath`, `code.lineno`), granular step-by-step pipeline events, decision markers, and dual execution paths (Positive Path vs. Negative Path).

---

## 3. Considered Options

1. **Option 1: Traditional Axios/Fetch Wrappers with Imperative Loops**
   * *Pros*: Simple to write initially.
   * *Cons*: Difficult to trace call stacks, prone to thundering herd, breaks pure functional constraints, prone to missing retry idempotency.

2. **Option 2: Class-based OOP Middleware Chain with Switch/Case Conditionals**
   * *Pros*: Familiar object-oriented pattern.
   * *Cons*: Relies heavily on mutable state, switch statements violate data-driven registry directives, lacks automatic stack frame line number extraction.

3. **Option 3: Pure Functional ScalableHttpClient with Data-Driven Registries & OTEL Telemetry (SELECTED)**
   * *Pros*: Zero mutable loops, Singleflight request collapsing, endpoint/header cache control, automatic `getCallerInfo()` call stack extraction, full step-by-step OTEL span event tracing.

---

## 4. Decision Outcome

**Chosen Option**: Option 3 (Pure Functional `ScalableHttpClient` with Data-Driven Registries & OTEL Telemetry).

### Architectural Key Mechanics:

#### A. Singleflight Request Collapsing
Identical in-flight GET requests map to a shared promise stored in `inFlightSingleflights`. Upon resolution or rejection, the promise resolves for all callers simultaneously while issuing exactly 1 network call.

#### B. OpenTelemetry Code Location Telemetry
Using stack frame extraction (`getCallerInfo()`), every span created by the HTTP client automatically attaches OTEL Semantic Conventions:
* `code.function`: Function/method name initiating the call.
* `code.filepath`: File path where the call originated.
* `code.lineno`: Exact line number where the call originated.

#### C. Granular Step-by-Step & Decision Telemetry
Spans emit structured events at each execution phase:
1. `step.request_interceptors_executed`
2. `step.header_providers_resolved`
3. `decision.cache_evaluated`
4. `decision.circuit_breaker_evaluated`
5. `step.fetch_attempt_initiated`
6. `step.response_interceptors_executed`
7. `decision.retry_evaluated`
8. `execution.success` (Positive Path: `SpanStatusCode.OK`) / `execution.failure` (Negative Path: `SpanStatusCode.ERROR`)

---

## 5. Consequences

### Positive
* **Zero Thundering Herds**: Deduplicates identical concurrent read queries seamlessly.
* **End-to-End Tracing Visibility**: Developers can immediately inspect OpenTelemetry traces to identify the exact line of code (`code.lineno`) that initiated any request and view every intermediate decision event.
* **Idempotent Resilience**: Preserves `x-idempotency-key` across Full Jitter exponential retries to prevent duplicate server mutations.
* **100% Type-Safe & Constant-Enforced**: Compiles with zero hardcoded string literals.

### Negative
* **Slight Tracing Payload Overhead**: Attaching detailed step events increases span memory footprint slightly. This is mitigated by asynchronous batch span processing (`BatchSpanProcessor`) in production.

---

## 6. Verification and Compliance

* **Unit Test Suite**: Verified by Vitest test suite in [`packages/node/shared-infra/src/http/tests/http-client.test.ts`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/node/shared-infra/src/http/tests/http-client.test.ts).
* **Feature Test Suites**: Passes 100% across all feature test suites (`overview`, `traces`, `costs`, `quality`).
