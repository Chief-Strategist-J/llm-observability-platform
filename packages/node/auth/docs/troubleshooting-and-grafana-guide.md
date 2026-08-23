# Troubleshooting & Grafana Tempo Debugging Guide

This guide provides end-to-end instructions for running Grafana, searching traces using TraceQL, filtering by time ranges, debugging authentication & database failures, and resolving common operational issues across `@observability/auth` and `@observability/web-app`.

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
3. Select Query Type:
   - **Search UI Tab**: Use dropdown selectors for Service Name (`web-app`, `auth-service`) and Span Name.
   - **Trace ID Tab**: Paste a 32-character hex Trace ID directly from HTTP response headers for instant lookup.
   - **TraceQL Tab**: Write declarative TraceQL filter expressions.
4. Adjust the **Time Range Selector** in top-right corner (Last 5 minutes, Last 15 minutes, Last 1 hour).

---

## 3. TraceQL Query Library for Debugging

> Note: In Tempo TraceQL, resource attributes use `resource.service.name` and span attributes use `.attribute_name` or `span.attribute_name`.

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
- **Web App Dashboard Route Latency (`/costs`)**:
  ```traceql
  { resource.service.name = "web-app" && name = "HTTP GET /costs" }
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

### Issue 2: "Grafana Explore UI Returns 0 Series Returned"
- **Symptom**: Grafana UI returns `0 series returned` when querying by TraceQL.
- **Root Cause**: Query syntax used unindexed custom brackets or missing resource prefixes.
- **Solution / Fix**:
  1. For service filtering, use `resource.service.name = "web-app"` instead of `.service.name`.
  2. For request lookup, use **Trace ID** tab with the exact 32-character hex ID from the HTTP `traceparent` response header.

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

### Issue 4: "Next.js Route Traces Missing in Grafana Tempo (`/costs`)"
- **Symptom**: Requests to `http://localhost:31400/costs` execute successfully, but no server spans appear in Tempo.
- **Root Cause**: `typeof window === 'undefined'` guard blocked Node.js OpenTelemetry initialization on Next.js server boot.
- **Solution / Fix**:
  1. Ensure `initOpenTelemetryTracer()` in `web-app/src/core/tracing/tracer.ts` dynamically imports `@observability/core/tracing` for Node.js server side.
  2. Verify Next.js `middleware.ts` extracts or generates `traceparent` and `x-request-id` headers on both request and response pipelines.

---

### Issue 5: "PostgreSQL Database Connection Terminated / Fatal Pool Error"
- **Symptom**: Server returns `HTTP 500` with `Connection terminated unexpectedly` or `FATAL: terminating connection`.
- **Root Cause**: Database pool connection dropped due to PostgreSQL process restart or idle timeout.
- **Solution / Fix**:
  Verify PostgreSQL container status on port `31412`:
  ```bash
  docker ps | grep auth-service-db
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
    "user": {
      "id": "usr_99s3cqn",
      "email": "jaydeep@gmail.com",
      "name": "Jaydeep",
      "org_id": "org_yiu4z6f",
      "org_name": "Scaibu",
      "role": "admin"
    }
  },
  "error": null
}
```

---

### Step 2: Query Grafana Tempo Direct Trace ID
```bash
curl -s -u admin:admin 'http://localhost:31415/api/datasources/proxy/uid/P214B5B846CF3925F/api/traces/cfa926f3d5688f652da89e6ef4deee18'
```

---

## 6. Visualizing Spans in Grafana (What the Trace Waterfall Looks Like)

When searching Grafana Tempo by Request Key or opening the Trace ID link, Grafana renders a single unified end-to-end trace waterfall:

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
