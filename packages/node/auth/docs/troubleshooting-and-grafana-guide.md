# 🔍 Troubleshooting & Grafana Tempo Debugging Guide

This guide provides end-to-end instructions for running Grafana, searching traces using TraceQL, filtering by time ranges, debugging authentication & database failures, and resolving common operational issues across `@observability/auth`.

---

## 🚀 1. Accessing & Running Grafana & Tempo

| Component | Endpoint / Port | Description | Credentials |
| :--- | :--- | :--- | :--- |
| **Grafana HTTPS Gateway** | `https://llmobs.grafana:31419` | SSL Ingress for Grafana Portal | `admin / admin` |
| **Grafana HTTP Direct** | `http://localhost:31415` | Local direct web interface | `admin / admin` |
| **OTEL Collector OTLP HTTP** | `http://localhost:31417/v1/traces` | Span ingestion endpoint | N/A |
| **OTEL Collector OTLP gRPC** | `localhost:31418` | High-throughput gRPC ingestion | N/A |
| **Tempo Direct Query** | `http://localhost:31416` (Port 3200) | Direct Tempo trace API | N/A |

---

## 🎛️ 2. How to Search & Filter in Grafana Explore

1. Navigate to **Grafana Explore**: `http://localhost:31415/explore` (or `https://llmobs.grafana:31419/explore`).
2. Select Datasource: **Tempo** (`P214B5B846CF3925F`).
3. Set Query Type to **TraceQL**.
4. Adjust the **Time Range Selector** in top-right corner:
   - Quick ranges: **Last 5 minutes**, **Last 15 minutes**, **Last 1 hour**.
   - Custom range: Specify start and end timestamps.

---

## 📚 3. TraceQL Query Library for Debugging

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
  { span.error.code = "INVALID_CREDENTIALS" }
  ```
- **Search by Validation Errors (Zod Schema Failure)**:
  ```traceql
  { span.error.code = "VALIDATION_ERROR" }
  ```

---

### C. Performance & Latency Analysis
- **Slow Requests (> 500ms)**:
  ```traceql
  { resource.service.name = "auth-service" && duration > 500ms }
  ```
- **High-Latency Database Queries (> 100ms)**:
  ```traceql
  { span.db.system = "postgresql" && duration > 100ms }
  ```

---

### D. User & Request Correlation Tracing
- **Filter Traces by User Email**:
  ```traceql
  { span.user.email = "devuser@example.com" }
  ```
- **Filter Traces by Request ID**:
  ```traceql
  { span.x-request-id = "req-1787491177230-g4lb89" }
  ```
- **Filter Traces by Correlation ID**:
  ```traceql
  { span.x-correlation-id = "corr-101" }
  ```

---

### E. Infrastructure & Message Queue Tracing
- **PostgreSQL Database Child Spans**:
  ```traceql
  { span.db.system = "postgresql" }
  ```
- **Kafka Event Producer & Consumer Spans**:
  ```traceql
  { span.messaging.system = "kafka" }
  ```

---

## 🛠️ 4. Common Operational Issues & Troubleshooting Matrix

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

### Issue 2: "No Traces Showing up in Grafana Tempo"
- **Symptom**: Querying `{ resource.service.name = "auth-service" }` returns empty results (`{"traces": []}`).
- **Root Cause**:
  1. Time range filter in Grafana is set outside the active span window (e.g. `Last 6 hours` when trace occurred 1 minute ago).
  2. OpenTelemetry `BatchSpanProcessor` holds spans in buffer for 5 seconds before dispatching.
- **Solution / Fix**:
  - Set Grafana Time Range to **Last 5 minutes**.
  - Wait 5 seconds after executing a request and click **Run Query**.

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
