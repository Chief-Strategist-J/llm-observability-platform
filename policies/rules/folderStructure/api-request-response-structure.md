# Standardized API Request & Response Structure Specification
*(Strictly Language-Agnostic Specification for Go, Python, Rust, Java, C++, Node.js/TypeScript, and C#)*

---

### Core Rules

1. **Language-Agnostic Principle**: This architecture specification is strictly **language-agnostic**. The header contracts, request/response envelopes, error dictionaries, ASCII decision trees, and context propagation algorithms apply identically regardless of whether the service is implemented in Go, Python, Rust, Java, C++, Node.js/TypeScript, or C#.
2. **Unified Envelope Contract**: Every HTTP REST and GraphQL JSON response (both success and error) MUST wrap payload contents inside a standardized envelope containing root-level `success`, `statusCode`, `data`/`error`, and `meta` blocks.
3. **Mandatory Header Identifiers**: Every request MUST carry and forward `traceparent`, `tracestate`, `x-request-id`, `x-correlation-id`, `x-causation-id`, `x-idempotency-key`, `x-tenant-id`, and `x-client-id`.
4. **Idempotent Operations**: All mutating POST, PUT, PATCH, and DELETE operations MUST respect `x-idempotency-key` to prevent duplicate processing on client retries or network retransmissions.

---

### Standardized Identifier Header Dictionary

| Header Key | Format / Example | Description | Requirement |
| :--- | :--- | :--- | :--- |
| `traceparent` | `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01` | OpenTelemetry W3C Distributed Trace Context | **Mandatory** (Auto-generated if missing) |
| `tracestate` | `rojo=1,congo=4` | Vendor-specific trace state baggage | Optional |
| `x-request-id` | `req-1700000000000-a1b2c3` | Unique ID generated per single HTTP execution | **Mandatory** |
| `x-correlation-id` | `corr-1700000000000-x9y8z7` | Unique ID persisted across an entire multi-service business flow | **Mandatory** |
| `x-causation-id` | `evt-1700000000000-k3m4p5` | Unique ID of the direct parent event/action causing this execution | **Mandatory for Event-Driven Steps** |
| `x-idempotency-key` | `idem-1700000000000-m5n6p7` | Unique key to guarantee single-execution mutation semantics | **Mandatory for Mutations** |
| `x-tenant-id` | `tenant-12345` | Multi-tenant isolation key | **Mandatory in Multi-Tenant Contexts** |
| `x-client-id` | `client-web-app-v1` | Identifies calling service or client application | Optional |
| `x-user-id` | `usr_99812` | Authenticated subject identity ID | Optional |

---

### ASCII Decision Tree — Request Processing, Idempotency & Tracing Flow

```log
└── Request Lifecycle Execution
    ├── 1. Extract Header Identifiers
    │   ├── Check `traceparent` → present? Use incoming trace context : Generate new W3C traceparent
    │   ├── Check `x-request-id` → present? Use incoming request ID : Generate `req-{timestamp}-{hash}`
    │   ├── Check `x-correlation-id` → present? Pass forward : Set `x-correlation-id = x-request-id`
    │   ├── Check `x-causation-id` → present? Pass forward : Set `x-causation-id = x-request-id`
    │   └── Check `x-idempotency-key` → present? Pass forward : Set `x-idempotency-key = x-request-id`
    │
    ├── 2. Idempotency Check (Mutations: POST / PUT / PATCH / DELETE)
    │   ├── Read `IdempotencyStore.get(x-idempotency-key)`
    │   ├── Record EXISTS → Return cached response envelope immediately (HttpStatus 200/201) with header `x-cache-hit: true`
    │   └── Record MISS → Acquire lock on `x-idempotency-key` → proceed to domain execution
    │
    ├── 3. Domain Execution inside OpenTelemetry Span
    │   ├── Start OpenTelemetry Span: `http.request {path}` with attributes:
    │   │   ├── `http.method`, `http.route`, `messaging.system`
    │   │   └── `x-request-id`, `x-correlation-id`, `x-causation-id`, `x-tenant-id`
    │   ├── Execute Domain Logic / Query Execution
    │   └── Handle Outcome:
    │       ├── SUCCESS:
    │       │   ├── Build `ApiResponse<T>` envelope with `meta` block
    │       │   ├── Store envelope in `IdempotencyStore` (TTL: 86400s)
    │       │   └── Set Span Status: `OK`
    │       └── FAILURE:
    │           ├── Build `ApiErrorResponse` envelope with canonical error code & details
    │           ├── Do NOT cache failed responses in `IdempotencyStore`
    │           └── Set Span Status: `ERROR` + record exception details
    │
    └── 4. Response Dispatch
        ├── Inject `traceparent`, `x-request-id`, `x-correlation-id` into outbound response headers
        └── Send JSON response envelope to client
```

---

### Standardized Response Envelopes

#### Success Response Envelope (`ApiResponse<T>`)

```json
{
  "success": true,
  "statusCode": 200,
  "data": {
    "userId": "usr_99812",
    "email": "user@example.com",
    "orgId": "org_55102",
    "status": "active"
  },
  "meta": {
    "requestId": "req-1700000000000-a1b2c3",
    "correlationId": "corr-1700000000000-x9y8z7",
    "causationId": "evt-1700000000000-k3m4p5",
    "timestamp": "2026-08-23T13:10:00.000Z",
    "executionTimeMs": 12
  }
}
```

#### Paginated Success Response Envelope (`ApiPaginatedResponse<T>`)

```json
{
  "success": true,
  "statusCode": 200,
  "data": [
    { "userId": "usr_99812", "email": "user1@example.com" },
    { "userId": "usr_99813", "email": "user2@example.com" }
  ],
  "meta": {
    "requestId": "req-1700000000000-a1b2c3",
    "correlationId": "corr-1700000000000-x9y8z7",
    "causationId": "evt-1700000000000-k3m4p5",
    "timestamp": "2026-08-23T13:10:00.000Z",
    "executionTimeMs": 24,
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalItems": 142,
      "totalPages": 8,
      "hasNextPage": true,
      "hasPreviousPage": false,
      "nextCursor": "eyJpZCI6InVzcl85OTgxMyJ9"
    }
  }
}
```

#### Error Response Envelope (`ApiErrorResponse`)

```json
{
  "success": false,
  "statusCode": 400,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "One or more payload validation checks failed.",
    "details": [
      {
        "field": "email",
        "issue": "Invalid email address format."
      },
      {
        "field": "password",
        "issue": "Password must be at least 8 characters long."
      }
    ]
  },
  "meta": {
    "requestId": "req-1700000000000-a1b2c3",
    "correlationId": "corr-1700000000000-x9y8z7",
    "causationId": "evt-1700000000000-k3m4p5",
    "timestamp": "2026-08-23T13:10:00.000Z",
    "executionTimeMs": 4
  }
}
```

---

### Canonical Error Code Dictionary

| Error Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `BAD_REQUEST` | 400 | Malformed request body or missing parameters |
| `VALIDATION_FAILED` | 400 | Field schema validation constraint violations |
| `UNAUTHENTICATED` | 401 | Invalid or missing authentication credentials / token |
| `FORBIDDEN` | 403 | Insufficient RBAC/ABAC permissions for requested resource |
| `NOT_FOUND` | 404 | Target entity or API route does not exist |
| `CONFLICT` | 409 | Entity unique constraint collision or duplicate write attempt |
| `UNPROCESSABLE_ENTITY` | 422 | Business rule / state machine transition rejection |
| `TOO_MANY_REQUESTS` | 429 | Rate limit quota exceeded |
| `INTERNAL_SERVER_ERROR` | 500 | Unhandled internal exception |
| `SERVICE_UNAVAILABLE` | 503 | Dependent downstream service or database unavailable |

---

### Language-Agnostic Pseudocode Algorithm

```log
ALGORITHM ProcessApiRequest(request, handler):
    1. EXTRACT headers:
       traceparent    := request.headers.get("traceparent") OR GenerateW3CTraceparent()
       request_id     := request.headers.get("x-request-id") OR GenerateId("req")
       correlation_id := request.headers.get("x-correlation-id") OR request_id
       causation_id   := request.headers.get("x-causation-id") OR request_id
       idempotency_key:= request.headers.get("x-idempotency-key") OR request_id
       tenant_id      := request.headers.get("x-tenant-id") OR "tenant-default"
       user_id        := request.headers.get("x-user-id") OR "anonymous"

    2. INITIALIZE Context(request_id, correlation_id, causation_id, idempotency_key, tenant_id, traceparent)

    3. IF request.method IN ["POST", "PUT", "PATCH", "DELETE"]:
           cached_envelope := IdempotencyStore.Get(idempotency_key)
           IF cached_envelope IS NOT NULL:
               RETURN cached_envelope WITH header("x-cache-hit", "true")

    4. START OpenTelemetry Span "http.request" WITH traceparent AND attributes(request_id, correlation_id, tenant_id)
       start_time := CurrentTimestampMs()

    5. TRY:
           payload := handler(request.body)
           execution_time := CurrentTimestampMs() - start_time
           
           envelope := ApiResponse(
               success = TRUE,
               statusCode = 200,
               data = payload,
               meta = Meta(request_id, correlation_id, causation_id, timestamp_iso(), execution_time)
           )

           IF request.method IN ["POST", "PUT", "PATCH", "DELETE"]:
               IdempotencyStore.Set(idempotency_key, envelope, ttl_seconds = 86400)

           FinishSpan(span, status = "OK")
           RETURN envelope

       CATCH Exception error:
           execution_time := CurrentTimestampMs() - start_time
           
           error_envelope := ApiErrorResponse(
               success = FALSE,
               statusCode = MapErrorToHttpStatus(error),
               error = ErrorDetail(
                   code = MapErrorToCanonicalCode(error),
                   message = error.message,
                   details = error.details
               ),
               meta = Meta(request_id, correlation_id, causation_id, timestamp_iso(), execution_time)
           )

           FinishSpan(span, status = "ERROR", exception = error)
           RETURN error_envelope
END ALGORITHM
```

---

### Cross-Protocol Header & Identifier Mapping

| REST Header Key | gRPC Metadata Key | Kafka Header Key |
| :--- | :--- | :--- |
| `traceparent` | `traceparent` | `traceparent` |
| `tracestate` | `tracestate` | `tracestate` |
| `x-request-id` | `x-request-id` | `requestId` |
| `x-correlation-id` | `x-correlation-id` | `correlationId` |
| `x-causation-id` | `x-causation-id` | `causationId` |
| `x-idempotency-key` | `x-idempotency-key` | `idempotencyKey` |
| `x-tenant-id` | `x-tenant-id` | `tenantId` |
| `x-user-id` | `x-user-id` | `userId` |
