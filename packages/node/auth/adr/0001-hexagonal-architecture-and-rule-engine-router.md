# ADR 0001: Hexagonal Architecture & Declarative Rule Engine Router

- **Status**: Accepted
- **Date**: 2026-08-23
- **Context**: The `@observability/auth` service requires strict separation of concerns between HTTP delivery, core domain rules, security mechanisms, and database persistence, as well as an extensible route matcher that eliminates repetitive conditional statements.

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
        RuleRouter["AuthRestV1Router (Engine)"]
        RuleRegistry["ROUTE_RULES (Data Registry)"]
        AuthCore["AuthService (Domain Core)"]
        SecurityEngine["13-Pillar Security Engine"]

        Server --> RuleRouter
        RuleRouter --> RuleRegistry
        RuleRouter --> AuthCore
        AuthCore --> SecurityEngine
    end

    subgraph InfrastructureLayer["Infrastructure Adapters"]
        AlloyDB[("AlloyDB / Postgres DB (:31412)")]
        RedisStore[("Redis Token Denylist (:31413)")]
        KafkaBroker["Kafka Messaging Broker (:31414)"]
    end

    WebApp -->|HTTP REST| Traefik
    ExternalAPI -->|Bearer JWT / API Key| Traefik
    Traefik -->|Route /api/v1/auth| Server

    AuthCore -->|SQL Queries| AlloyDB
    AuthCore -->|Session Revocation Check| RedisStore
    AuthCore -->|Publish Auth Events| KafkaBroker
```

---

## 🔬 Low-Level Design (LLD)

```mermaid
sequenceDiagram
    autonumber
    participant HTTP as Node.js HTTP Server
    participant Router as AuthRestV1Router
    participant Rules as ROUTE_RULES Registry
    participant Handler as Route Handler
    participant Domain as AuthService Engine
    participant DB as AlloyDB Adapter

    HTTP->>Router: route(method, path, body, headers, queryParams)
    Router->>Router: Wrap with OpenTelemetry Span ("REST {method} {path}")
    Router->>Rules: findMatchingRule(method, path)
    Rules-->>Router: Matched Rule + Extracted Path Parameters
    
    alt Rule Requires Auth
        Router->>Domain: handleVerifySession(authHeader)
        Domain-->>Router: Verified Session Payload
    end

    Router->>Handler: rule.handler(ctx, session)
    Handler->>Domain: Invoke core domain method
    Domain->>DB: Execute SQL persistence query
    DB-->>Domain: SQL result set
    Domain-->>Handler: Domain result
    Handler-->>Router: Response data payload
    Router-->>HTTP: HTTP { statusCode, payload: createSuccessResponse(...) }
```

---

## 📋 Architectural Decisions & Trade-Offs

1. **Separation of Router Data vs Engine Logic**:
   - `route.rules.ts` contains strictly declarative data configuration mapping HTTP methods and path patterns to handler functions.
   - `router.ts` contains strictly executable engine logic (regex path matching, trace span wrapping, central session validation, error handling).

2. **Compiled Regex Path Matcher**:
   - Route path patterns like `/api/v1/auth/organizations/:id/switch` are pre-compiled into regular expressions at router instantiation for high-performance matching.
