# Troubleshooting & Grafana Tempo Debugging Guide

This guide provides end-to-end instructions for running Grafana, searching traces using TraceQL, filtering by time ranges, debugging authentication & database failures, and resolving common operational issues across `@observability/auth`.

---

## 1. Accessing & Running Grafana & Tempo

| Component | Endpoint / Port | Description | Credentials |
| :--- | :--- | :--- | :--- |
| **Grafana HTTPS Gateway** | `https://llmobs.grafana:31419` | SSL Ingress for Grafana Portal | `admin / admin` |
| **Grafana HTTP Direct** | `http://localhost:31415` | Local direct web interface | `admin / admin` |
| **OTEL Collector OTLP HTTP** | `http://localhost:31417/v1/traces` | Span ingestion endpoint | N/A |
| **OTEL Collector OTLP gRPC** | `localhost:31418` | High-throughput gRPC ingestion | N/A |
| **Tempo Direct Query** | `http://localhost:31416` (Port 3200) | Direct Tempo trace API | N/A |

---

## 2. How to Search & Filter in Grafana Explore

1. Navigate to **Grafana Explore**: `http://localhost:31415/explore` (or `https://llmobs.grafana:31419/explore`).
2. Select Datasource: **Tempo** (`P214B5B846CF3925F`).
3. Set Query Type to **TraceQL**.
4. Adjust the **Time Range Selector** in top-right corner:
   - Quick ranges: **Last 5 minutes**, **Last 15 minutes**, **Last 1 hour**.
   - Custom range: Specify start and end timestamps.

---

## 3. TraceQL Query Library for Debugging

> Note: In Tempo TraceQL, span attributes use dot prefixes (e.g. `{.x-request-id = "value"}`) rather than `span.`.

### A. General Service Traces
- **All Auth Service Spans**:
  ```traceql
  { resource.service.name = "auth-service" }
  ```
- **All Web App Spans**:
  ```traceql
  { resource.service.name = "web-app" }
  ```

---

### B. Error & Failure Debugging
- **All Errors in Auth Service**:
  ```traceql
  { resource.service.name = "auth-service" && status = error }
  ```
- **Search by Specific Error Code (e.g. Invalid Password)**:
  ```traceql
  { .error.code = "INVALID_CREDENTIALS" }
  ```
- **Search by Validation Errors (Zod Schema Failure)**:
  ```traceql
  { .error.code = "VALIDATION_ERROR" }
  ```

---

### C. Performance & Latency Analysis
- **Slow Requests (> 500ms)**:
  ```traceql
  { resource.service.name = "auth-service" && duration > 500ms }
  ```
- **High-Latency Database Queries (> 100ms)**:
  ```traceql
  { .db.system = "postgresql" && duration > 100ms }
  ```

---

### D. User & Request Correlation Tracing
- **Filter Traces by Request ID / Request Key**:
  ```traceql
  { .x-request-id = "req-root-test-001" }
  ```
- **Filter Traces by Correlation ID**:
  ```traceql
  { .x-correlation-id = "corr-clean-101" }
  ```
- **Filter Traces by User Email**:
  ```traceql
  { .user.email = "jaydeep@gmail.com" }
  ```

---

### E. Infrastructure & Message Queue Tracing
- **PostgreSQL Database Child Spans**:
  ```traceql
  { .db.system = "postgresql" }
  ```
- **Kafka Event Producer & Consumer Spans**:
  ```traceql
  { .messaging.system = "kafka" }
  ```

---

## 4. Common Operational Issues & Troubleshooting Matrix

### Issue 1: "CORS Error in Browser / Network Tab Options Preflight Blocked"
- **Symptom**: Browser throws CORS preflight rejection when calling `http://localhost:3001/api/v1/auth/sign-in` or pushing traces to `http://localhost:31417/v1/traces`.
- **Root Cause**: Custom headers (`x-request-id`, `x-correlation-id`, `traceparent`) not explicitly allowed in server CORS config.
- **Solution / Fix**:
  Check `AUTH_CONSTANTS.SECURITY_CONFIG.CORS_HEADERS` in `auth.constants.ts` or `otel-collector-config.yaml`:
  ```typescript
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': '*',
  'Access-Control-Expose-Headers': 'traceparent, tracestate, x-request-id, x-correlation-id',
  ```

---

### Issue 2: "TraceQL Syntax Error: unknown identifier: span"
- **Symptom**: Grafana UI returns `0 series returned` or `unknown identifier: span` when typing `{ span.x-request-id = "val" }`.
- **Root Cause**: Tempo TraceQL requires span attributes to be prefixed with a dot (`.x-request-id`) instead of `span.`.
- **Solution / Fix**:
  Use `{.x-request-id = "req-root-test-001"}` or `{.user.email = "jaydeep@gmail.com"}`.

---

### Issue 3: "Disconnected Trace Waterfall / Separate Trace IDs"
- **Symptom**: Client request and server request render as two separate isolated traces instead of a single waterfall graph.
- **Root Cause**: Missing W3C `traceparent` context extraction on server entrypoint or missing header injection on client fetcher.
- **Solution / Fix**:
  - **Client (`auth-client.ts`)**: Inject trace context:
    ```typescript
    propagation.inject(context.active(), headers);
    ```
  - **Server (`middleware.ts`)**: Extract trace context:
    ```typescript
    const extractedContext = propagation.extract(ROOT_CONTEXT, req.headers, defaultTextMapGetter);
    context.with(extractedContext, () => { tracer.startActiveSpan(...) });
    ```

---

### Issue 4: "PostgreSQL Database Connection Terminated / Fatal Pool Error"
- **Symptom**: Server returns `HTTP 500` with `Connection terminated unexpectedly` or `FATAL: terminating connection`.
- **Root Cause**: Database pool connection dropped due to PostgreSQL process restart or idle timeout.
- **Solution / Fix**:
  Verify PostgreSQL container status on port `31412`:
  ```bash
  docker ps | grep auth-service-db
  ```
  If container dropped, restart:
  ```bash
  docker restart auth-service-db
  ```

---

### Issue 5: "Kafka Event Producer Operating in Fallback Mode"
- **Symptom**: Console logs warning `[kafka-producer] Operating in fallback mode: Connection refused`.
- **Root Cause**: Kafka broker on `localhost:9092` / container `frontend-kafka:31414` unreachable.
- **Solution / Fix**:
  Verify Kafka container status:
  ```bash
  docker ps | grep frontend-kafka
  ```

---

## 5. End-to-End Tracing via `curl` with Request Keys & JSON Responses

### Step 1: Execute Sign-In Request with Explicit Request Key
```bash
curl -s -X POST http://localhost:3001/api/v1/auth/sign-in \
  -H "Content-Type: application/json" \
  -H "x-request-id: req-root-test-001" \
  -H "x-correlation-id: corr-root-test-001" \
  -d '{"email":"jaydeep@gmail.com","password":"Scaibu@123456"}'
```

**JSON Response Payload Returned**:
```json
{
  "status": "success",
  "message": "User signed in successfully",
  "data": {
    "token": "eyJzdWIiOiJ1c3JfOTlzM2NxbiIsImVtYWlsIjoiamF5ZGVlcEBnbWFpbC5jb20iLCJvcmciOnsib3JnX2lkIjoib3JnX3lpdTR6NmYiLCJvcmdfbmFtZSI6IlNjYWlidSIsInJvbGUiOiJhZG1pbiJ9LCJpYXQiOjE3ODc0OTI0NDEsImV4cCI6MTc4NzQ5NjA0MX0=.c2lnX3Vzcl85OXMzY3FuXzE3ODc0OTI0NDE=",
    "payload": {
      "sub": "usr_99s3cqn",
      "email": "jaydeep@gmail.com",
      "org": {
        "org_id": "org_yiu4z6f",
        "org_name": "Scaibu",
        "role": "admin"
      },
      "exp": 1787496041,
      "iat": 1787492441
    },
    "user": {
      "id": "usr_99s3cqn",
      "email": "jaydeep@gmail.com",
      "name": "Jaydeep",
      "org_id": "org_yiu4z6f",
      "org_name": "Scaibu",
      "role": "admin",
      "blocked": false,
      "user_permissions": [
        "admin:all"
      ]
    }
  },
  "error": null
}
```

---

### Step 2: Query Grafana Tempo TraceQL API for Request Key (`req-root-test-001`)
```bash
curl -s -u admin:admin 'http://localhost:31415/api/datasources/proxy/uid/P214B5B846CF3925F/api/search?q=%7B.x-request-id%3D%22req-root-test-001%22%7D'
```

**JSON Response Payload Returned**:
```json
{
  "traces": [
    {
      "traceID": "cfa926f3d5688f652da89e6ef4deee18",
      "rootServiceName": "auth-service",
      "rootTraceName": "HTTP POST /api/v1/auth/sign-in",
      "startTimeUnixNano": "1787492441750000000",
      "durationMs": 34,
      "spanSet": {
        "spans": [
          {
            "spanID": "b0e9c4d34d3b1412",
            "startTimeUnixNano": "1787492441750000000",
            "attributes": [
              { "key": "x-request-id", "value": { "stringValue": "req-root-test-001" } }
            ]
          }
        ],
        "matched": 2
      },
      "serviceStats": {
        "auth-service": { "spanCount": 3 }
      }
    }
  ],
  "metrics": {
    "inspectedBytes": "535788",
    "completedJobs": 3,
    "totalJobs": 3
  }
}
```

---

### Step 3: Query Grafana Tempo Directly for Trace ID (`cfa926f3d5688f652da89e6ef4deee18`)
```bash
curl -s -u admin:admin 'http://localhost:31415/api/datasources/proxy/uid/P214B5B846CF3925F/api/traces/cfa926f3d5688f652da89e6ef4deee18'
```

---

## 6. Visualizing Spans in Grafana (What the Trace Waterfall Looks Like)

When searching Grafana Tempo by Request Key (`{.x-request-id = "req-root-test-001"}`) or opening the Trace ID link, Grafana renders a single unified end-to-end trace waterfall:

```text
Grafana Tempo Trace Waterfall Graph [Trace ID: cfa926f3d5688f652da89e6ef4deee18]
-----------------------------------------------------------------------------------------------
Service & Span Name                        Kind     Duration   Attributes                   
-----------------------------------------------------------------------------------------------
[OK] web-app: authApiClient.signIn          CLIENT   38ms       user.email=jaydeep@gmail.com 
 `-- [OK] auth-service: HTTP POST /sign-in   SERVER   34ms       x-request-id=req-root-test-001
      `-- [OK] auth-service: REST POST      INTERNAL 32ms       route.name=SIGN_IN           
           |-- [OK] DB SELECT findUserByEmail CLIENT 12ms       db.system=postgresql         
           |-- [OK] Argon2id Password Check  INTERNAL 15ms       crypto.algorithm=argon2id    
           |-- [OK] DB INSERT recordAuditLog  CLIENT   3ms        db.system=postgresql         
           `-- [OK] Kafka PRODUCE USER_IN    PRODUCER 2ms        topic=auth.events.v1         
                `-- [OK] Kafka CONSUMER      CONSUMER 1ms        messaging.operation=process  
-----------------------------------------------------------------------------------------------
```

#### If a Failure Occurs (e.g. Wrong Password):
```text
Grafana Tempo Error Trace Waterfall Graph [Trace ID: 7ddc5fc112278d5075421c35704bea2e]
-----------------------------------------------------------------------------------------------
Service & Span Name                        Kind     Duration   Attributes / Error           
-----------------------------------------------------------------------------------------------
[ERROR] auth-service: HTTP POST /sign-in    SERVER   78ms       status=ERROR (HTTP 401)      
 `-- [ERROR] auth-service: REST POST       INTERNAL 75ms       error.code=INVALID_CREDENTIALS
      |-- [OK] DB SELECT findUserByEmail    CLIENT   14ms       db.system=postgresql         
      `-- [ERROR] Argon2id Password Check  INTERNAL 58ms       error="Invalid credentials"  
-----------------------------------------------------------------------------------------------
```
