# ADR 0002: Sign-Up, Sign-In, Argon2id Hashing, Kafka Event Pipeline & Audit Logging

- **Status**: Accepted
- **Date**: 2026-08-23
- **Context**: User registration (Sign-Up) and authentication (Sign-In) must provide secure password hashing using Argon2id, atomic user & organization creation, structured audit logging, JWT session token generation, and asynchronous Kafka event publishing.

---

## 🏛 High-Level Design (HLD)

```mermaid
flowchart TD
    subgraph Client["Client Application"]
        UI["Web App Auth Form"]
        Saga["Redux Auth Saga"]
    end

    subgraph Service["Auth Microservice (:3001)"]
        Router["Rule Engine Router"]
        AuthHandler["Auth REST Handler"]
        DomainCore["AuthService Core"]
        ArgonEngine["Argon2id Password Engine"]
        JWTEngine["JWT Token Generator"]
        KafkaProducer["AuthEventProducer Pipeline"]
    end

    subgraph Messaging["Kafka Messaging Broker (:31414)"]
        KafkaTopic["Topic: auth.events (USER_SIGNED_UP / USER_SIGNED_IN)"]
    end

    subgraph Persistence["AlloyDB / PostgreSQL Storage (:31412)"]
        UsersTable[("auth_users Table")]
        OrgsTable[("auth_organizations Table")]
        MappingsTable[("auth_user_organizations Table")]
        AuditLogsTable[("auth_audit_logs Table")]
    end

    UI -->|Submit Form| Saga
    Saga -->|POST /api/v1/auth/sign-up or sign-in| Router
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
```

---

## 🔬 Low-Level Design (LLD)

### 1. Sign-Up Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client Application
    participant Router as AuthRestV1Router
    participant Service as AuthService Engine
    participant Argon as Argon2id Engine
    participant DB as AlloyDB / PostgreSQL
    participant Kafka as Kafka Event Pipeline

    Client->>Router: POST /api/v1/auth/sign-up { email, password, name, organization_name }
    Router->>Service: handleSignUp(input)
    Service->>DB: Check if email exists in auth_users
    DB-->>Service: Email status (Not found)

    Service->>Argon: hashPassword(password)
    Argon-->>Service: Argon2id Hash String ($argon2id$v=19$...)

    Service->>DB: BEGIN Transaction
    Service->>DB: INSERT INTO auth_organizations (org_id, name, slug)
    Service->>DB: INSERT INTO auth_users (user_id, email, password_hash, name)
    Service->>DB: INSERT INTO auth_user_organizations (user_id, org_id, role)
    Service->>DB: COMMIT Transaction

    Service->>Kafka: publishUserSignedUp({ userId, email, orgId })
    Kafka-->>Service: Event published to topic auth.events

    Service->>Service: Issue Scoped JWT (sub: user_id, org_id, role: owner)
    Service-->>Router: Return { status: "success", token, user }
    Router-->>Client: HTTP 201 Created Response Payload
```

---

### 2. Sign-In & Verification Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client Application
    participant Router as AuthRestV1Router
    participant Service as AuthService Engine
    participant Argon as Argon2id Engine
    participant DB as AlloyDB / PostgreSQL
    participant Kafka as Kafka Event Pipeline

    Client->>Router: POST /api/v1/auth/sign-in { email, password }
    Router->>Service: handleSignIn(input, headers)
    Service->>DB: SELECT * FROM auth_users WHERE email = $1 AND deleted_at IS NULL
    DB-->>Service: User record + password_hash + is_blocked flag

    alt User is blocked or deleted
        Service-->>Router: Throw AuthError ("User account is blocked")
        Router-->>Client: HTTP 403 Forbidden Response
    end

    Service->>Argon: verifyPassword(inputPassword, storedHash)
    
    alt Password Mismatch
        Service-->>Router: Throw AuthError ("Invalid email or password")
        Router-->>Client: HTTP 401 Unauthorized Response
    else Password Match
        Service->>DB: INSERT INTO auth_audit_logs (user_id, event_type, ip_address, user_agent)
        Service->>Kafka: publishUserSignedIn({ userId, email, orgId })
        Kafka-->>Service: Event published to topic auth.events
        Service->>Service: Issue Scoped JWT Token
        Service-->>Router: Return { status: "success", token, user }
        Router-->>Client: HTTP 200 OK Response Payload
    end
```

---

## 📋 Architectural Principles & Guarantees

1. **Argon2id Standard**: Password verification enforces Argon2id with memory cost and time cost parameters to prevent GPU brute-force attacks.
2. **Atomic Multi-Entity Transactions**: Sign-up executes user creation, organization initialization, and N-to-N membership mapping inside an atomic PostgreSQL database transaction.
3. **Structured Audit Trail & Kafka Events**: Every sign-in attempt captures IP address and user-agent string into `auth_audit_logs` and emits real-time `USER_SIGNED_IN` / `USER_SIGNED_UP` events over Kafka.
