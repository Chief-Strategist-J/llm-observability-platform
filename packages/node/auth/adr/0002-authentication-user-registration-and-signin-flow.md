# ADR 0002: Sign-Up, Sign-In, Argon2id Hashing, OpenTelemetry Tracing & Audit Logging

- **Status**: Accepted
- **Date**: 2026-08-23
- **Context**: User registration (Sign-Up) and authentication (Sign-In) must provide secure password hashing using Argon2id, atomic user & organization creation, structured audit logging, JWT session token generation, end-to-end W3C trace context propagation, and asynchronous Kafka event publishing.

---

## 🏛 High-Level Design (HLD)

```mermaid
flowchart TD
    subgraph Client["Client Application (web-app)"]
        UI["Web App Auth Form"]
        Saga["Redux Auth Saga"]
        AuthClient["RawAuthApiClient (W3C Inject)"]
    end

    subgraph Service["Auth Microservice (:3001)"]
        Middleware["traceHttpMiddleware (W3C Extract)"]
        Router["Rule Engine Router (Span Error & Attribute Tagging)"]
        AuthHandler["Auth REST Handler"]
        DomainCore["AuthService Core"]
        ArgonEngine["Argon2id Password Engine"]
        JWTEngine["JWT Token Generator"]
        KafkaProducer["AuthEventProducer (W3C Header Inject)"]
    end

    subgraph Messaging["Kafka Messaging Broker (:31414)"]
        KafkaTopic["Topic: auth.events.v1 (USER_SIGNED_UP / USER_SIGNED_IN)"]
    end

    subgraph Persistence["AlloyDB / PostgreSQL Storage (:31412)"]
        UsersTable[("auth_users Table (DB Client Spans)")]
        OrgsTable[("auth_organizations Table")]
        MappingsTable[("auth_user_organizations Table")]
        AuditLogsTable[("auth_audit_logs Table")]
    end

    subgraph Telemetry["Observability Infrastructure"]
        OTELCollector["frontend-otel-collector (:31417)"]
        Tempo["Grafana Tempo (:3200 / :31415)"]
    end

    UI -->|Submit Form| Saga
    Saga --> AuthClient
    AuthClient -->|POST /sign-in + traceparent| Middleware
    Middleware --> Router
    Router --> AuthHandler
    AuthHandler --> DomainCore

    DomainCore --> ArgonEngine
    DomainCore --> JWTEngine
    DomainCore -->|Publish Kafka Event| KafkaProducer
    KafkaProducer -->|Publish Event| KafkaTopic

    DomainCore -->|Insert / Verify User| UsersTable
    DomainCore -->|Create Organization| OrgsTable
    DomainCore -->|Map User Role| MappingsTable
    DomainCore -->|Log Sign-In Event| AuditLogsTable

    Middleware -->|Export OTLP Spans| OTELCollector
    OTELCollector --> Tempo
```

---

## 🔬 Low-Level Design (LLD)

### 1. Sign-Up Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client Application (web-app)
    participant MW as traceHttpMiddleware
    participant Router as AuthRestV1Router
    participant Service as AuthService Engine
    participant Argon as Argon2id Engine
    participant DB as AlloyDB / PostgreSQL
    participant Kafka as Kafka Event Pipeline

    Client->>MW: POST /api/v1/auth/sign-up (traceparent, x-request-id)
    MW->>MW: Extract W3C traceparent & start SERVER span
    MW->>Router: handleSignUp(input)
    Router->>Service: executeSignUp()
    Service->>DB: Check if email exists (DB Client Span)
    DB-->>Service: Email status (Not found)

    Service->>Argon: hashPassword(password)
    Argon-->>Service: Argon2id Hash String ($argon2id$v=19$...)

    Service->>DB: BEGIN Transaction (DB Client Span)
    Service->>DB: INSERT INTO auth_organizations
    Service->>DB: INSERT INTO auth_users
    Service->>DB: INSERT INTO auth_user_organizations
    Service->>DB: COMMIT Transaction

    Service->>Kafka: publishUserSignedUp({ userId, email, orgId })
    Kafka->>Kafka: Inject traceparent into message headers

    Service->>Service: Issue Scoped JWT
    Service-->>Router: Return { status: "success", token, user }
    Router-->>Client: HTTP 201 Created Response Payload
```

---

### 2. Sign-In Sequence Flow (With Error Span Handling)

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client Application (web-app)
    participant MW as traceHttpMiddleware
    participant Router as AuthRestV1Router
    participant Service as AuthService Engine
    participant Argon as Argon2id Engine
    participant DB as AlloyDB / PostgreSQL
    participant Collector as OTEL Collector (:31417)

    Client->>MW: POST /api/v1/auth/sign-in (traceparent, x-request-id)
    MW->>MW: Extract W3C traceparent & start SERVER span
    MW->>Router: route("POST", "/api/v1/auth/sign-in")
    Router->>Router: Tag user.email, x-request-id, x-correlation-id
    Router->>Service: signIn(email, password)
    Service->>DB: findUserByEmail(email) [DB Client Span]
    DB-->>Service: User Record

    alt Password Mismatch / Incorrect Credentials
        Service->>Argon: verifyPasswordHash(password, hash) -> False
        Service-->>Router: Throw AuthError("INVALID_CREDENTIALS")
        Router->>Router: Set span.setStatus(ERROR) & span.recordException(err)
        Router-->>MW: Return HTTP 401 Response
        MW->>Collector: Export ERROR Span to Tempo
    else Valid Password
        Service->>Argon: verifyPasswordHash(password, hash) -> True
        Service->>Service: Issue Scoped JWT Token
        Service-->>Router: Return { status: "success", token }
        Router-->>Client: HTTP 200 OK Response Payload
    end
```

---

## 🌳 End-to-End Function Call Stack (ASCII Tree)

```tree
User Clicks "Sign In" Button / Executes API Request
└── 1. RawAuthApiClient.execute('signIn', payload) [src/lib/auth-client.ts]
    ├── Injects W3C Header: traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
    ├── Injects Header: x-request-id: req-1787491177230-g4lb89
    └── Injects Header: x-correlation-id: req-1787491177230-g4lb89
        │
        ├── [HTTP Network Boundary: POST http://localhost:3001/api/v1/auth/sign-in] ──>
        │
        └── 2. server.ts :: http.createServer handler
            └── 3. middleware.ts :: traceHttpMiddleware(req, res)
                ├── Extract incoming `traceparent` via propagation.extract(ROOT_CONTEXT, headers)
                └── Start Active SERVER Span: `HTTP POST /api/v1/auth/sign-in`
                    │
                    └── 4. router.ts :: AuthRestV1Router.route("POST", "/api/v1/auth/sign-in")
                        └── withSpan("REST POST /api/v1/auth/sign-in")
                            ├── Tag Attribute: `user.email = jaydeep@gmail.com`
                            ├── Tag Attribute: `x-request-id = req-1787491177230-g4lb89`
                            ├── Tag Attribute: `x-correlation-id = req-1787491177230-g4lb89`
                            │
                            └── 5. service.ts :: AuthService.signIn(email, password)
                                ├── 6. real-postgres-auth.adapter.ts :: findUserByEmail(email)
                                │   └── withSpan("DB SELECT findUserByEmail", kind: CLIENT)
                                │       └── Execute PostgreSQL SQL Query (Port 31412)
                                │
                                ├── 7. argon2id.ts :: verifyPasswordHash(password, hash)
                                │   └── [Failure Mode] If mismatch: Set SpanStatus.ERROR & recordException
                                │
                                └── 8. auth-event.producer.ts :: publishUserSignedIn()
                                    ├── Inject traceparent into Kafka message headers
                                    └── Publish to Kafka Topic `auth.events.v1` (Port 31414)
```
