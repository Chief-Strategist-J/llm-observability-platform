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

## 🌳 Complete End-to-End Functional Call Stack (ASCII Tree)

```tree
User clicks "Sign In" button (Frontend User Action)
└── SignUpForm / SignInForm.tsx [src/features/auth/ui/SignInForm.tsx]
    └── handleSubmit(e) [Form Event Handler]
        └── onSubmit({ email, password }) [Prop Callback]
            └── SignInPage.handleSubmit() [src/app/auth/sign-in/page.tsx]
                └── dispatch(authActions.signInSubmitted({ email, password })) [Redux Action Dispatch]
                    │
                    ├── 1. authSlice.reducers.signInSubmitted() [src/features/auth/auth.slice.ts]
                    │   └── Updates Redux State -> state.auth.status = 'loading'
                    │
                    └── 2. rootSaga -> authSaga Watcher [src/features/auth/auth.saga.ts]
                        └── takeEvery(authActions.signInSubmitted.type, handleSignIn)
                            └── handleSignIn(action) [Redux-Saga Generator]
                                └── authApiClient.signIn(payload) [src/lib/auth-client.ts]
                                    │
                                    ├── 3. Resilient Adapter Decorator Chain [src/core/data-driven/adapter-decorators.ts]
                                    │   └── withTracing -> withCircuitBreaker -> withCache -> withRetry
                                    │
                                    └── 4. RawAuthApiClient.execute('signIn', { body }) [src/lib/auth-client.ts]
                                        ├── Inject W3C Header: traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
                                        ├── Inject Header: x-request-id: req-1787491177230-g4lb89
                                        ├── Inject Header: x-correlation-id: req-1787491177230-g4lb89
                                        │
                                        └── fetch('http://localhost:3001/api/v1/auth/sign-in', { method: 'POST', body })
                                            │
                                            ├── [HTTP Network Request Wire] ──> [Backend Auth Service :3001]
                                            │   └── http.createServer [server.ts]
                                            │       └── traceHttpMiddleware [middleware.ts] (Extract W3C traceparent)
                                            │           └── AuthRestV1Router.route() [router.ts]
                                            │               ├── Tag Attribute: user.email = devuser@example.com
                                            │               ├── Tag Attribute: x-request-id = req-1787491177230-g4lb89
                                            │               │
                                            │               └── AuthService.signIn() [service.ts] (Facade)
                                            │                   └── UserAuthDomainService.signIn() [services/user-auth.service.ts] (SRP Engine)
                                            │                       │
                                            │                       ├── a. SignInInputSchema.parse(input) [schema/auth.schema.ts]
                                            │                       ├── b. RealPostgresAuthAdapter.findUserByEmail() [real-postgres-auth.adapter.ts]
                                            │                       │   ├── withSpan('DB SELECT findUserByEmail', kind: CLIENT)
                                            │                       │   ├── pool.connect() [pg Pool]
                                            │                       │   ├── client.query(AUTH_QUERIES.FLOW_SIGN_IN.FIND_USER_BY_EMAIL) [auth.queries.ts]
                                            │                       │   └── client.release() [pg Pool]
                                            │                       ├── c. verifyPassword(password, user.password_hash) [shared/utils/argon2.util.ts]
                                            │                       │   └── [Failure Mode] If mismatch: Set SpanStatus.ERROR & recordException
                                            │                       ├── d. RealPostgresAuthAdapter.recordAuditLog() [real-postgres-auth.adapter.ts]
                                            │                       │   ├── pool.connect() [pg Pool]
                                            │                       │   ├── client.query(AUTH_QUERIES.TENANT_RLS.SET_LOCAL_TENANT_CONTEXT) [RLS Context]
                                            │                       │   ├── client.query(AUTH_QUERIES.FLOW_SIGN_IN.RECORD_AUDIT_LOG) [Insert Log]
                                            │                       │   └── client.release() [pg Pool]
                                            │                       ├── e. createToken(userId, email, orgDetails) [shared/utils/jwt.util.ts]
                                            │                       ├── f. verifyToken(token) [shared/utils/jwt.util.ts]
                                            │                       └── g. AuthEventProducer.publishUserSignedIn() [auth-event.producer.ts]
                                            │                           └── ProducerMiddlewarePipeline.execute() [messaging-middleware.ts]
                                            │                               ├── loggingProducerMiddleware() [Logger]
                                            │                               ├── tracingProducerMiddleware() [OpenTelemetry Spans]
                                            │                               └── CentralizedKafkaClient.publishToTopic('auth.events.v1') [Kafka :31414]
                                            │
                                            └── ON RESPONSE SUCCESS (200 OK):
                                                ├── setAuthCookies(token, role) [document.cookie: authjs.session-token]
                                                ├── put(authActions.authSuccess({ user, organization })) [Redux State -> status: 'success']
                                                ├── eventBus.emit('auth.signInSuccess', response) [Cross-Feature Event Bus]
                                                └── useEffect() Status Watcher [src/app/auth/sign-in/page.tsx]
                                                    ├── router.push('/dashboard') [Next.js Router Navigation]
                                                    └── router.refresh() [Next.js Page Cache Refresh]
```
