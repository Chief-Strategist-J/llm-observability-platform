# ADR 0005: OpenTelemetry End-to-End Authentication Tracing & Middleware Architecture

- **Status**: Accepted
- **Date**: 2026-08-23
- **Author**: @Chief-Strategist-J
- **Scope**: `@observability/auth` tracing infrastructure, HTTP middleware, W3C trace propagation, and Grafana Tempo ingestion

---

## 1. Context & Problem Statement

The `@observability/auth` service executes critical authentication operations including user sign-in, user registration, JWT session verification, and session revocation. Previously, domain operations created internal spans via `withSpan`, but the service lacked a registered `NodeTracerProvider` and `OTLPTraceExporter`. Consequently, authentication traces were not dispatched to the OpenTelemetry Collector or Grafana Tempo storage. Additionally, incoming HTTP requests were not automatically intercepted at the HTTP server entrypoint.

---

## 2. Decision & Architecture Overview

1. **Active OTLP Exporter Initialization (`initAuthTracing`)**:
   - Initialized `NodeTracerProvider` with `resourceFromAttributes` using semantic conventions `service.name = 'auth-service'` and `service.version = '1.0.0'`.
   - Attached `BatchSpanProcessor` with `OTLPTraceExporter` configured to push spans to `http://localhost:31417/v1/traces`.

2. **HTTP Tracing Middleware (`traceHttpMiddleware`)**:
   - Mounted `traceHttpMiddleware` on the `http.createServer` entrypoint in `server.ts`.
   - Automatically wraps incoming HTTP requests in `SpanKind.SERVER` root spans (`HTTP POST /api/v1/auth/sign-in`, `HTTP POST /api/v1/auth/sign-up`, `HTTP GET /api/v1/auth/health`).

3. **Distributed Trace Propagation**:
   - Extracts and injects OpenTelemetry W3C trace context (`traceparent`, `tracestate`) across HTTP request boundaries, Kafka message headers, and database executions.

---

## 3. High-Level Architecture Diagram

```mermaid
graph TD
    Client["Client / Web-App Browser"] -->|HTTP POST /sign-in| AuthServer["Auth HTTP Server (Port 3001)"]
    
    subgraph Auth Microservice
        AuthServer --> Middleware["traceHttpMiddleware"]
        Middleware --> Router["AuthRestV1Router"]
        Router --> Service["AuthService"]
        Service --> DB["AlloyDB / PostgreSQL (Port 31412)"]
        Service --> Kafka["AuthEventProducer"]
    end
    
    Middleware -->|OTLP HTTP Spans| OTELCollector["frontend-otel-collector (Port 31417)"]
    OTELCollector -->|gRPC Spans| Tempo["frontend-tempo (Port 3200)"]
    Tempo -->|Trace Query| Grafana["Grafana Explore UI (Port 31415 / 31419)"]
```

---

## 4. Low-Level Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as Client Application
    participant Middleware as traceHttpMiddleware
    participant Router as AuthRestV1Router
    participant Service as AuthService
    participant Exporter as OTLPTraceExporter
    participant Collector as OTEL Collector (Port 31417)
    participant Tempo as Grafana Tempo (Port 3200)

    User->>Middleware: POST /api/v1/auth/sign-in (Headers: traceparent, x-request-id)
    Middleware->>Middleware: Start Active SERVER Span "HTTP POST /api/v1/auth/sign-in"
    Middleware->>Router: Route Request
    Router->>Router: Start Active INTERNAL Span "REST POST /api/v1/auth/sign-in"
    Router->>Service: signIn(email, password)
    Service-->>Router: Return JWT Session Token
    Router-->>Middleware: Return 200 OK Response Envelope
    Middleware->>Middleware: Set Span Status OK & End Span
    Middleware->>Exporter: Batch Export Spans
    Exporter->>Collector: POST /v1/traces (HTTP 31417)
    Collector->>Tempo: Export gRPC Spans (Port 3200)
    Tempo-->>User: Trace Queryable via TraceQL {resource.service.name="auth-service"}
```

---

## 5. End-to-End Call Stack Topology

```text
└── [Client / HTTP Request] POST http://localhost:3001/api/v1/auth/sign-in
    ├── 1. server.ts :: http.createServer handler
    │   └── 2. middleware.ts :: traceHttpMiddleware(req, res)
    │       ├── Extract incoming `traceparent` or generate new W3C traceparent
    │       └── Start Root Server Span: `HTTP POST /api/v1/auth/sign-in`
    │           ├── Attribute: `http.method = POST`
    │           ├── Attribute: `http.target = /api/v1/auth/sign-in`
    │           │
    │           └── 3. router.ts :: AuthRestV1Router.route("POST", "/api/v1/auth/sign-in")
    │               └── tracer.ts :: withSpan("REST POST /api/v1/auth/sign-in")
    │                   ├── Start Child Internal Span: `REST POST /api/v1/auth/sign-in`
    │                   │
    │                   └── 4. service.ts :: AuthService.signIn(email, password)
    │                       ├── 5. repository :: AuthRepositoryPort.findByEmail(email)
    │                       │   └── Execute SQL Query on PostgreSQL (Port 31412)
    │                       │
    │                       ├── 6. argon2id :: verifyPasswordHash(password, hash)
    │                       │
    │                       └── 7. producer :: AuthEventProducer.publish("USER_SIGNED_IN")
    │                           ├── Inject traceparent into Kafka Message Headers
    │                           └── Publish event to Kafka Topic `auth.events.v1` (Port 31414)
    │
    └── 8. tracer.ts :: BatchSpanProcessor -> OTLPTraceExporter
        ├── HTTP POST http://localhost:31417/v1/traces (frontend-otel-collector)
        └── Export gRPC -> frontend-tempo:3200 (Indexed for Grafana TraceQL Query)
```

---

## 6. Verification Results

- **Trace Search**: Verified via `curl -u admin:admin 'http://localhost:31415/api/datasources/proxy/uid/P214B5B846CF3925F/api/search?q=%7Bresource.service.name%3D%22auth-service%22%7D'`.
- **Captured Operations**: `REST POST /api/v1/auth/sign-in`, `REST POST /api/v1/auth/sign-up`, `REST GET /api/v1/auth/health`.
