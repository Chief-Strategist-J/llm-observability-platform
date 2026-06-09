# pytrace

One CLI. Zero code changes. Full system flow visibility for any Python service or distributed system.

## How it works under the hood
Three layers working together:
- **Layer 1** → OTel auto-instrumentation (HTTP, DB, gRPC, queues — zero code changes)
- **Layer 2** → bpftrace USDT (Python function call tree, syscalls)
- **Layer 3** → pytrace CLI (stitches both, renders the flow)

## Features

### 1. pytrace attach <pid>
Attach to any running Python process. No restart. No code changes. Starts collecting immediately.

```bash
pytrace attach 4821
```

### 2. pytrace flow
Renders the complete execution flow as a tree — your functions + every outbound call + every DB query, all nested correctly with timing.

```bash
pytrace flow --last
```

### 3. pytrace stitch
Stitches all traces across distributed services (Service A -> Service B -> Service C) into a single timeline using W3C traceparent.

```bash
pytrace stitch --services api,worker,ml-service
```

### 4. pytrace slow
Continuous background monitoring daemon that surfaces only the slow paths automatically.

```bash
pytrace slow --threshold 200ms --watch
```

### 5. pytrace diff
Compare execution flows and performance metrics before vs after a deployment.

```bash
pytrace diff --before deploy-v1.2 --after deploy-v1.3
```
