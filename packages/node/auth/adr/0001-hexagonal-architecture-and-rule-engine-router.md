# ADR 0001: Hexagonal Architecture & Declarative Rule Engine Router

- **Status**: Accepted
- **Date**: 2026-08-23
- **Context**: The `@observability/auth` service requires strict separation of concerns between HTTP delivery, core domain rules, security mechanisms, OpenTelemetry W3C distributed tracing, and database persistence, as well as an extensible route matcher that eliminates repetitive conditional statements.

---

## 🏛 High-Level Design (HLD)

```mermaid
flowchart TD
    subgraph Clients["Client Layer"]
        WebApp["Next.js Web App (:31400)"]
        ExternalAPI["External API Consumer"]
    end

    subgraph Gateway["Gateway & Proxy Layer"]
        Traefik["Traefik API Gateway (:31410 / :31411)"]
    end

    subgraph AuthModule["@observability/auth Service (:3001)"]
        Server["HTTP Server (server.ts)"]
        Middleware["traceHttpMiddleware (W3C Extract)"]
        RuleRouter["AuthRestV1Router (Engine)"]
        RuleRegistry["ROUTE_RULES (Data Registry)"]
        AuthCore["AuthService (Domain Core)"]
        SecurityEngine["13-Pillar Security Engine"]

        Server --> Middleware
        Middleware --> RuleRouter
        RuleRouter --> RuleRegistry
        RuleRouter --> AuthCore
        AuthCore --> SecurityEngine
    end

    subgraph InfrastructureLayer["Infrastructure Adapters"]
        AlloyDB[("AlloyDB / Postgres DB (:31412)")]
        RedisStore[("Redis Token Denylist (:31413)")]
        KafkaBroker["Kafka Messaging Broker (:31414)"]
        OTELCollector["OTEL Collector (:31417)"]
    end

    WebApp -->|HTTP REST + traceparent| Traefik
    ExternalAPI -->|Bearer JWT / API Key| Traefik
    Traefik -->|Route /api/v1/auth| Server

    Middleware -->|OTLP HTTP Spans| OTELCollector
    AuthCore -->|SQL Queries via DB Child Spans| AlloyDB
    AuthCore -->|Session Revocation Check| RedisStore
    AuthCore -->|Publish Auth Events with W3C Headers| KafkaBroker
```

---

## 🔬 Low-Level Design (LLD)

```mermaid
sequenceDiagram
    autonumber
    participant HTTP as Node.js HTTP Server
    participant Middleware as traceHttpMiddleware
    participant Router as AuthRestV1Router
    participant Rules as ROUTE_RULES Registry
    participant Handler as Route Handler
    participant Domain as AuthService Engine
    participant DB as AlloyDB Adapter (RealPostgresAuthAdapter)

    HTTP->>Middleware: Incoming Request (traceparent, x-request-id)
    Middleware->>Middleware: Extract W3C traceparent & start SERVER span
    Middleware->>Router: route(method, path, body, headers, queryParams)
    Router->>Router: Start INTERNAL span & tag user.email, x-request-id
    Router->>Rules: findMatchingRule(method, path)
    Rules-->>Router: Matched Rule + Extracted Path Parameters
    
    alt Rule Requires Auth
        Router->>Domain: handleVerifySession(authHeader)
        Domain-->>Router: Verified Session Payload
    end

    Router->>Handler: rule.handler(ctx, session)
    Handler->>Domain: Invoke core domain method
    Domain->>DB: Execute SQL persistence query (SpanKind.CLIENT)
    DB-->>Domain: SQL result set
    Domain-->>Handler: Domain result
    Handler-->>Router: Response data payload
    Router-->>Middleware: HTTP { statusCode, payload: createSuccessResponse(...) }
    Middleware->>Middleware: Set Span Status OK / ERROR & End Span
```

---

## 🌳 End-to-End Function Call Stack (ASCII Tree)

```tree
HTTP Request Received (Any Endpoint)
└── http.createServer [server.ts]
    └── traceHttpMiddleware(req, res) [infra/tracing/middleware.ts]
        ├── Extract W3C traceparent via propagation.extract(ROOT_CONTEXT, headers)
        └── Start Root SERVER Span ("HTTP {method} {path}")
            │
            └── AuthRestV1Router.route(method, path, body, headers, queryParams) [router.ts]
                │
                ├── 1. OpenTelemetry Span Start ("REST {method} {path}") [tracer.ts]
                │   ├── Tag Attribute: user.email (if present in payload)
                │   ├── Tag Attribute: x-request-id / x-correlation-id
                │   └── Set SpanStatus.ERROR on validation/auth failure
                │
                ├── 2. Match ROUTE_RULES Table [route.rules.ts]
                │   ├── Match HTTP Method ("GET" / "POST" / "DELETE")
                │   └── Match Pre-compiled Regex Path Pattern
                │
                ├── 3. Session Verification (If authRequired === true)
                │   ├── extractBearerToken(headers.authorization)
                │   └── UserAuthDomainService.validateSession(token) [services/user-auth.service.ts]
                │
                └── 4. Execute Rule Handler
                    └── AuthService Engine [service.ts]
                        └── RealPostgresAuthAdapter [infra/adapters/postgres/real-postgres-auth.adapter.ts]
                            └── withSpan("DB SELECT ...", kind: CLIENT)
```

---

## 🔐 CORS & Security Configuration

The server enforces wildcard CORS preflight handling (`Access-Control-Allow-Headers: *`) to ensure custom OpenTelemetry headers (`traceparent`, `tracestate`, `x-request-id`, `x-correlation-id`) are accepted seamlessly without preflight blocks.
