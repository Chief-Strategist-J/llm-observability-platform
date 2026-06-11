# pylow

**One CLI. Zero code changes. Full system flow visibility for any Python service or distributed system.**

Version `0.1.8` — 86 commands across kernel tracing, Python internals, JSON analysis, HTTP tooling, pipeline patterns, and distributed workflow orchestration.

---

## Installation & Setup

```bash
pip install pylow
```

> [!IMPORTANT]
> If you get `Command 'pylow' not found` after installation, your Python user bin directory is not on PATH.
> Fix it:
> ```bash
> echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
> source ~/.bashrc
> ```

---

## How It Works

Three layers working together:

```
Layer 1 → OTel auto-instrumentation  (HTTP, DB, gRPC, queues — zero code changes)
Layer 2 → bpftrace USDT              (Python function call tree, syscalls, kernel)
Layer 3 → pylow CLI                  (stitches both, renders the flow)
```

---

## Quick Start

```bash
# Find the PID of your process first
pgrep -f "your_app.py"

# Attach and start collecting
pylow attach <PID>

# Render the execution flow
pylow flow --last

# 10-second triage — tells you exactly what category problem you have
pylow triage <PID>
```

---

## Complete Command Reference

All 86 commands, grouped by category.

---

## CATEGORY 1 — Core Tracing

### `pylow attach <PID>`
Attach to any running Python process and start collecting trace logs.
```bash
pylow attach 4821
```
```
✓ Attached to process 4821. Monitoring execution events...
```

---

### `pylow flow [--last]`
Render the full execution flow tree from collected spans.
```bash
pylow flow --last
```
```
handle_request 450ms
├── authenticate_user 20ms
│   └── [redis GET session_id] 15ms
└── call_llm_chain 410ms
    └── [POST api.openai.com/v1/chat/completions] 400ms
        └── waiting (epoll_wait) 390ms   ← bottleneck
```

---

### `pylow stitch --services <list>`
Stitch distributed traces together across service boundaries.
```bash
pylow stitch --services api,worker,ml-service
```
```
REQUEST trace-id: t_demo_flow_123

  api-gateway     450ms  handle_request
  └── api-gateway  20ms  authenticate_user
      └── api-gateway  15ms  redis GET session_id
```

---

### `pylow slow [--threshold <ms>] [--watch]`
Surface slow execution paths exceeding a latency threshold.
```bash
pylow slow --threshold 200ms --watch
```
```
Continuous monitoring daemon started. Threshold: 200ms

SLOW PATHS detected (last 5 min):
  #1  handle_request → call_llm_chain → [waiting (epoll_wait)]
      avg: 390ms  occurrences: 1
      root cause: epoll_wait 310ms — network latency
```

---

### `pylow diff --before <id> --after <id>`
Compare execution flow metrics between two releases to detect regressions.
```bash
pylow diff --before deploy-v1.2 --after deploy-v1.3
```
```
REGRESSIONS:
  handle_request  +150ms avg  (was 200ms, now 350ms)
  serialize        +12ms avg  (was 3ms, now 15ms)

NEW CALLS in v1.3:
  validate_schema  8ms

REMOVED in v1.3:
  legacy_cache_check
```

---

## CATEGORY 2 — Kernel & Syscall Tracing

### `pylow syscall <PID>`
Trace syscall counts and histogram latency.
```bash
pylow syscall 4821
```
```
--- BPF Map: @sys_counts ---
  sys_enter_read: 231
  sys_enter_write: 184
  sys_enter_epoll_wait: 42
```

---

### `pylow malloc <PID>`
Profile memory allocation sizes and callers.
```bash
pylow malloc 4821
```
```
--- BPF Map: @alloc_sizes (bytes) ---
[64, 127]              45 |@@@@@@@@@@@                         |
[512, 1023]           120 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
[4096, 8191]           18 |@@@@                                |
```

---

### `pylow tcp <PID>`
Trace outbound TCP sendmsg latency.
```bash
pylow tcp 4821
```
```
--- BPF Map: @tcp_send_us (ns delay) ---
[100000, 200000]       21 |@@@@@@@@@@                          |
```

---

### `pylow io <PID>`
Trace File and Block I/O read/write latencies.
```bash
pylow io 4821
```
```
--- BPF Map: @read_lat (ns) ---
[4096, 8191]          150 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
[16384, 32767]         23 |@@@@@                               |
```

---

### `pylow flame <PID> [--duration <sec>]`
Generate CPU sampling flame graphs (SVG).
```bash
pylow flame 4821 --duration 5
```
```
✓ Sampling for 5s...
✓ Saved flame graph to flamegraph.svg
```

---

### `pylow sched <PID>`
Trace runqueue scheduler latency.
```bash
pylow sched 4821
```
```
--- BPF Map: @runq_latency_us ---
[1, 2]                 98 |@@@@@@@@@@@@@@@@@@@@@@@@            |
[4, 8]                142 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
```

---

### `pylow page-faults <PID>`
Trace page fault hotspots — which code is triggering cold memory access.
```bash
pylow page-faults 4821
```
```
=== PAGE FAULT HOTSPOTS ===
@faults[
    malloc+0x24
    PyBytes_FromStringAndSize+0x18
    load_dataset @ ml/data.py:12
]: 421
```

---

### `pylow context-switches <PID>`
Profile preemption and voluntary context switches.
```bash
pylow context-switches 4821
```
```
OFF CPU 87ms next_cpu=2

--- BPF Map: @off_cpu_ms ---
[0, 1]                12 |@@@@                                |
[64, 128]            210 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
```

---

### `pylow kernel-blocked <PID>`
Trace the exact kernel call path where the process is sleeping uninterruptibly.
```bash
pylow kernel-blocked 4821
```
```
BLOCKED IN KERNEL:
    futex_wait+0x120
    take_gil+0x42
    execute_query+0x91  db.py:102
```

---

### `pylow tlb-shootdowns <PID>`
Profile TLB flush rates and reasons.
```bash
pylow tlb-shootdowns 4821
```
```
--- BPF Map: @tlb_reason ---
[0] (TLB_FLUSH_ON_TASK_SWITCH)    42
[1] (TLB_FLUSH_ON_PAGE_FAULT)    187
```

---

### `pylow irq-impact <PID>`
Monitor soft and hard IRQ CPU cycles stolen from the process.
```bash
pylow irq-impact 4821
```
```
--- BPF Map: @sirq_type ---
[3] (NET_RX_SOFTIRQ)    187

--- BPF Map: @sirq_lat (us) ---
[8, 16]              187 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
```

---

## CATEGORY 3 — Python Runtime Tracing

### `pylow pycall <PID>`
Profile Python `PyObject_Call` function execution timings.
```bash
pylow pycall 4821
```
```
SLOW execute_query took 12400us
SLOW process_job took 1850us
```

---

### `pylow pyframe <PID>`
Trace exact Python frames: file, function name, line number.
```bash
pylow pyframe 4821
```
```
ENTER execute_query() @ db/models.py:142
slow_query() @ db/models.py:142 — p99: 340ms
```

---

### `pylow pycpu <PID>`
Identify CPU hotspots in Python stacks.
```bash
pylow pycpu 4821
```
```
--- BPF Map: @stacks ---
  → Resolved: call_llm_chain @ gateway/orchestrator.py:120  (145 samples)
```

---

### `pylow pyexcept <PID>`
Trace raised Python exceptions with user stack.
```bash
pylow pyexcept 4821
```
```
EXCEPTION KeyError @ tid=10234
  get_user_context @ db/client.py:48
```

---

### `pylow pyiowait <PID>`
Trace Python code blocking on I/O.
```bash
pylow pyiowait 4821
```
```
BLOCKING READ 12ms
  fetch_metadata @ db/client.py:54
```

---

### `pylow pygil <PID>`
Profile GIL acquisition delays and thread contention.
```bash
pylow pygil 4821
```
```
GIL WAIT 1250us tid=10234
  calculate_features @ ml/engine.py:89
```

---

### `pylow pyleak <PID>`
Profile heap allocations to detect memory leak patterns.
```bash
pylow pyleak 4821
```
```
=== TOP ALLOCATORS ===
@allocs[0x7f3b821034bc]: 10485760 bytes
  → load_dataset @ ml/data.py:12
```

---

### `pylow pyreq <PID>`
Measure end-to-end request lifecycle breakdown.
```bash
pylow pyreq 4821
```
```
REQ START tid=10234
REQ DONE total=340ms db=310ms other=30ms
```

---

### `pylow timeline <PID> [--duration <sec>] [--threshold <ms>]`
Render a chronological timeline call graph with entry/exit timestamps.
```bash
pylow timeline 4821 --duration 5.0 --threshold 2.0
```
```
[     0.000ms] → handle_request()  server.py:45
[     0.040ms]   → parse_headers()  http.py:12
[     0.051ms]   ← parse_headers()  [0.011ms]
[    91.230ms]   ← execute_query()  [91.175ms]  ⚠️ SLOW
```

---

### `pylow pythread <PID>`
Trace thread-aware function call timelines with self-time per thread.
```bash
pylow pythread 4821
```
```
--- Thread ID: 10001 ---
  parse_headers() spent 0.00ms (Self time: 0.00ms)
```

---

### `pylow pyasync <PID>`
Trace async coroutine suspend/resume metrics.
```bash
pylow pyasync 4821
```
```
--- Coroutine: 0x7f3b821034bc ---
  Suspended counts: 2
  Total CPU Time: 80us
```

---

### `pylow pyargs <PID>`
Profile Python function call argument types and layout (CPython struct dereference).
```bash
pylow pyargs 4821
```
```
1000 CALL obj=0x7f3b821034bc args=0x7f3b821051fa
```

---

### `pylow pysyscall <PID>`
Profile syscalls attributed directly to Python frames.
```bash
pylow pysyscall 4821
```
```
=== SLOW READ fd=4 dur=12ms ===
  fetch_metadata @ db/client.py:54
```

---

### `pylow pynplus1 <PID>`
Detect N+1 query loop patterns from ORM calls.
```bash
pylow pynplus1 4821
```
```
⚠️  N+1 CANDIDATE: db/models.py:142
   Called 15x in 5s (3.0/s)
```

---

### `pylow pygraph <PID>`
Trace hierarchical call relationships as a call graph.
```bash
pylow pygraph 4821
```
```
handle_request()  calls=1  avg=0.00ms  (server.py:45)
  execute_query()  calls=1  avg=0.00ms  (db.py:88)
```

---

### `pylow pyanomaly <PID>`
Identify statistically anomalous slow function calls vs baseline.
```bash
pylow pyanomaly 4821
```
```
[BASELINE] execute_query(): mean=10.33ms stddev=0.76ms
🚨 ANOMALY execute_query(): 45.00ms vs baseline 10.33ms
```

---

### `pylow pydash <PID>`
Stream live function call metrics to a curses dashboard.
```bash
pylow pydash 4821
```
```
=== LIVE FUNCTION TRACER ===
RECENT CALLS:
  handle_request() 120.40ms
```

---

### `pylow pysingle <PID> <func>`
Trace a single function's complete execution tree with self-time.
```bash
pylow pysingle 4821 handle_request
```
```
[     0.000ms] → handle_request()  server.py:45
[     0.011ms]   → validate_token()  auth.py:12
[     0.015ms]   ← validate_token()  total=0.004ms  self=0.003ms
```

---

## CATEGORY 4 — Diagnostic Workflows

### `pylow triage <PID>`
Run a 10-second triage profile. Tells you exactly which problem category to investigate.
```bash
pylow triage 4821
```
```
cpu_samples : 842    ← high → CPU BOUND
off_cpu     : 12
syscalls    : 234
page_faults : 8

→ DIAGNOSIS: CPU BOUND — use pylow cpu-bound 4821
```

---

### `pylow cpu-bound <PID>`
Full CPU-bound diagnostic: hottest stacks + duration attribution.
```bash
pylow cpu-bound 4821
```
```
CPU HOTSPOT: call_llm_chain @ gateway/orchestrator.py:120
  Samples: 145 / 200 total (72.5%)
  Avg duration: 1240ms
```

---

### `pylow io-bound <PID>`
Full I/O-bound diagnostic: blocking syscall + Python origin stack.
```bash
pylow io-bound 4821
```
```
BLOCKED syscall=read 87ms
  fetch_metadata @ db/client.py:54
  → fd=7 → /var/run/postgresql/.s.PGSQL.5432
```

---

### `pylow syscall-storm <PID> [--id <syscall_id>]`
Diagnose high-frequency syscall storm. Optionally filter to a specific syscall ID.
```bash
pylow syscall-storm 4821
pylow syscall-storm 4821 --id 1   # filter to sys_write only
```
```
TOP SYSCALLS (5s):
  id=1 (write)   3841 calls
  id=0 (read)    1204 calls
  id=202 (futex)  892 calls
```

---

### `pylow deadlock <PID>`
Detect deadlocks: locks acquired but never released within the observation window.
```bash
pylow deadlock 4821
```
```
=== LOCKS HELD > 5s ===
@lock[tid=10234, lock=0x7f3b820f1234]: held since 8234ms
  → PyThread_acquire_lock @ db/connection_pool.py:88
```

---

### `pylow service-map <PID>`
Map inbound and outbound request flow: connections, bytes in/out.
```bash
pylow service-map 4821
```
```
=== SERVICE pid=4821 ===
outbound_calls : 14
bytes_in       : 204800
bytes_out      : 81920
conn_time_ms:
  [10, 20]     8 |@@@@@@@@@@@@                        |
```

---

### `pylow ordered-log <PID> [--filter-internals]`
Output a chronological ordered log of every Python function call and return.
```bash
pylow ordered-log 4821
pylow ordered-log 4821 --filter-internals   # strip CPython bootstrap noise
```
```
1749558821000001  ENTER  handle_request          server.py:45
1749558821000040  ENTER  authenticate_user        auth.py:12
1749558821000055  EXIT   authenticate_user
1749558821000060  ENTER  execute_query            db.py:88
1749558821091000  EXIT   execute_query            91ms ⚠️ SLOW
```

---

### `pylow intercept <PID> [func]`
Intercept entry/exit payloads at a boundary function. Shows file, line, tid, stack.
```bash
pylow intercept 4821 process_payment
```
```
=== process_payment CALLED ===
file : payments/service.py
line : 142
tid  : 10234
time : 1749558821000060

=== process_payment RETURNED ===
duration: 88ms
```

---

### `pylow anomaly-trigger <PID> [func]`
Arm a trigger on a function — capture full call tree only when an exception or anomaly fires.
```bash
pylow anomaly-trigger 4821 validate_payment
```
```
[WATCHING] validate_payment — armed, zero noise until trigger

!!! EXCEPTION DURING PAYMENT !!!
type  : ValueError
after : 23ms
  → process_refund @ payments/service.py:89
  → validate_payment @ payments/service.py:34
```

---

### `pylow correlation <PID> [service_name]`
Trace cross-service chronological correlation. Stamp every call with service name + nanosecond timestamp.
```bash
pylow correlation 4821 api-gateway
# Run simultaneously on all service PIDs, then merge:
# cat /tmp/trace_*.log | sort -k2 -t=
```
```
SVC=api-gateway TS=1749558821000001 ENTER handle_request server.py:45
SVC=api-gateway TS=1749558821000040 CONNECT
SVC=api-gateway TS=1749558821000060 EXIT  handle_request
```

---

## CATEGORY 5 — HTTP & API Tooling

### `pylow curl-perf <PID> [url]`
Trace HTTP request timing breakdown: DNS, connect, TTFB, total.
```bash
pylow curl-perf 4821 https://api.example.com/payments
```
```
=== HTTP PERFORMANCE: https://api.example.com/payments ===
  time_namelookup  :   0.012s
  time_connect     :   0.031s
  time_starttransfer:  0.087s
  time_total       :   0.091s
  http_code        :   200
  size_download    :   4096 bytes
```

---

### `pylow jwt-decode <PID>`
Intercept and decode JWT Authorization tokens inline from HTTP headers.
```bash
pylow jwt-decode 4821
```
```
=== JWT DECODED ===
Header : {"alg":"RS256","typ":"JWT"}
Payload: {"sub":"user_9821","exp":1749645221,"roles":["admin"]}
Expiry : 2026-06-12T06:00:21Z (valid)
```

---

### `pylow cert-check <PID> [domain]`
Trace SSL/TLS handshake and certificate expiry for a domain.
```bash
pylow cert-check 4821 api.example.com
```
```
=== TLS CERTIFICATE: api.example.com ===
  Subject : CN=api.example.com
  Issuer  : Let's Encrypt Authority X3
  Expires : 2026-09-01T00:00:00Z
  Days left: 82
  Status  : ✓ VALID
```

---

### `pylow rate-limit-test <PID>`
Diagnose API rate limit backoff — detect HTTP 429 responses and retry delays.
```bash
pylow rate-limit-test 4821
```
```
HTTP 429 received — Retry-After: 60s
Backoff attempt 1/3 — waiting 60s
Backoff attempt 2/3 — waiting 120s
Total blocked time: 180s
```

---

### `pylow parallel-fetch <PID> [--concurrency <n>]`
Trace parallel request pipelines and concurrent connection activity.
```bash
pylow parallel-fetch 4821 --concurrency 8
```
```
Active parallel workers: 8
Fetched 10 payment details in parallel (duration: 120ms)
Successfully processed items: 10/10
```

---

## CATEGORY 6 — Shell Pipeline Patterns

### `pylow jq-search <PID> [query]`
Search JSON stream for field names or patterns.
```bash
pylow jq-search 4821 error
```
```
Searching stream for "error"...
  .actStatus.name = "ERROR"
  .response.errorCode = "PAYMENT_FAILED"
```

---

### `pylow awk-stats <PID>`
Compute statistics (count, sum, avg, min, max, percentages) on tabular data streams.
```bash
pylow awk-stats 4821
```
```
=== STREAM STATISTICS ===
  count : 1042
  sum   : 94821ms
  avg   : 91.0ms
  min   : 12ms
  max   : 3421ms
  p95   : 340ms
```

---

### `pylow tee-branch <PID>`
Monitor output stream branching — writes to multiple sinks simultaneously.
```bash
pylow tee-branch 4821
```
```
Stream branching active:
  → stdout     (live display)
  → /tmp/response.log  (file capture)
  Bytes written: 40960
```

---

### `pylow pipe-decouple <PID> [fifo_path]`
Monitor named pipe FIFO decoupler. Shows producer/consumer throughput.
```bash
pylow pipe-decouple 4821 /tmp/payment_pipe
```
```
Named pipe: /tmp/payment_pipe
  Producer writes: 412
  Consumer reads : 409
  Buffer lag     : 3 items
```

---

### `pylow sed-mask <PID>`
Monitor stream for PII masking rules applied by sed filters.
```bash
pylow sed-mask 4821
```
```
=== MASKING ACTIVE ===
  Pattern: [0-9]{16}       → CARD-XXXX-XXXX-XXXX-XXXX
  Pattern: \b[\w.]+@[\w.]+\b → EMAIL-MASKED
  Lines processed: 1042
  Patterns matched: 87
```

---

## CATEGORY 7 — JSON Response Analysis

All `jq-*` commands analyze live JSON responses from the traced process. Pass a `pid` to attach.

---

### `pylow jq-schema <PID>`
Discover the full recursive type schema of a JSON response (shape only, no values).
```bash
pylow jq-schema 4821
```
```json
{
  "id": "number",
  "actStatus": { "id": "number", "name": "string" },
  "refLinkTo": { "id": "number", "payModes": "null" }
}
```

---

### `pylow jq-nulls <PID>`
List all null fields as a flat array of dotted key paths.
```bash
pylow jq-nulls 4821
```
```json
["newconconno", "newconleadsid", "reminderdate", "actStatus.salesActivities"]
```

---

### `pylow jq-null-paths <PID>`
Same as `jq-nulls` with full dotted path for nested nulls.
```bash
pylow jq-null-paths 4821
```
```
actStatus.salesActivities = null
refLinkTo.payModes = null
reminderdate = null
```

---

### `pylow jq-locate-key <PID> [key]`
Find all paths in the document tree that contain a given key name.
```bash
pylow jq-locate-key 4821 salesActivities
```
```
Paths containing "salesActivities":
  .actStatus.salesActivities
  .refLinkTo.actStatus.salesActivities
```

---

### `pylow jq-key-path <PID> [key]`
Find all paths and their values for a given key name.
```bash
pylow jq-key-path 4821 name
```
```
.actStatus.name = "COMPLETED"
.refLinkTo.name = "PAYMENT_MODE_CASH"
```

---

### `pylow jq-all-keys <PID>`
Discover the full vocabulary of unique keys across the entire document.
```bash
pylow jq-all-keys 4821
```
```
All unique keys (32):
  id, enddate, actStatus, name, salesActivities, refLinkTo,
  payModes, reminderdate, newconconno, ...
```

---

### `pylow jq-leaf-paths <PID> [--filter-val <term>]`
List all leaf (non-object) paths with their values. Optionally filter.
```bash
pylow jq-leaf-paths 4821
pylow jq-leaf-paths 4821 --filter-val COMPLETED
```
```
.id = 28920212268
.enddate = "2026-06-10"
.actStatus.name = "COMPLETED"
```

---

### `pylow jq-clean-nulls <PID>`
Output the response with all null fields removed.
```bash
pylow jq-clean-nulls 4821
```
```json
{
  "id": 28920212268,
  "enddate": "2026-06-10",
  "actStatus": { "id": 1, "name": "COMPLETED" }
}
```

---

### `pylow jq-depth-map <PID>`
Calculate nesting depth per key branch across the entire document.
```bash
pylow jq-depth-map 4821
```
```
Root depth: 1
  actStatus: depth=2
    salesActivities: depth=3
  refLinkTo: depth=2
    payModes: depth=3
```

---

### `pylow jq-type-map <PID>`
Map every leaf path to its resolved data type.
```bash
pylow jq-type-map 4821
```
```
.id              → number
.enddate         → string
.actStatus.name  → string
.refLinkTo.payModes → null
```

---

### `pylow jq-find-value <PID> [value]`
Find the exact path where a specific value occurs.
```bash
pylow jq-find-value 4821 gravity_admin
```
```
Value "gravity_admin" found at:
  .createdBy.username
  .modifiedBy.username
```

---

### `pylow jq-structural-diff <PID>`
Compare two response snapshots and show added/removed/changed fields.
```bash
pylow jq-structural-diff 4821
```
```
STRUCTURAL DIFF:
  ADDED   : .actStatus.resolvedAt
  REMOVED : .legacyFlag
  CHANGED : .actStatus.name  (PENDING → COMPLETED)
```

---

### `pylow jq-extract-subtree <PID> [key]`
Surgically extract a subtree from the document by key name.
```bash
pylow jq-extract-subtree 4821 appModulesId
```
```json
{
  "appModulesId": {
    "id": 5,
    "name": "PAYMENT_MODULE",
    "active": true
  }
}
```

---

### `pylow jq-summary <PID>`
Print response statistics: total keys, null count, max depth, array sizes.
```bash
pylow jq-summary 4821
```
```
=== RESPONSE SUMMARY ===
  Total keys   : 47
  Null fields  : 12  (25.5%)
  Max depth    : 4
  Arrays       : 3
  Largest array: salesActivities (0 items — empty)
```

---

### `pylow jq-validate-schema <PID> [schema_file]`
Validate the response structure against a JSON schema template file.
```bash
pylow jq-validate-schema 4821 schema.json
```
```
Schema validation against schema.json:
  ✓ id            present
  ✓ actStatus     present
  ✗ paymentRef    MISSING
  Result: INVALID — 1 field missing
```

---

### `pylow jq-array-schema <PID>`
Inspect all arrays: their sizes and the schema of their items.
```bash
pylow jq-array-schema 4821
```
```
.salesActivities  : 0 items  (empty)
.paymentHistory   : 3 items  → {id: number, date: string, amount: number}
.tags             : 5 items  → string
```

---

### `pylow jq-null-pct <PID>`
Calculate the percentage of null fields relative to total fields.
```bash
pylow jq-null-pct 4821
```
```
Null field percentage: 25.5%
  Total fields : 47
  Null fields  : 12
  Filled fields: 35
```

---

### `pylow jq-non-null-leaves <PID>`
List only the fields that have actual non-null values.
```bash
pylow jq-non-null-leaves 4821
```
```
Non-null leaves (35):
  .id = 28920212268
  .enddate = "2026-06-10"
  .actStatus.name = "COMPLETED"
  ...
```

---

### `pylow jq-parent-context <PID> [key]`
Show a key along with its parent object and sibling fields for context.
```bash
pylow jq-parent-context 4821 salesActivities
```
```
Key: salesActivities
Parent: actStatus
Siblings:
  id   = 1
  name = "COMPLETED"
  salesActivities = null  ← target
```

---

### `pylow jq-locate-value-contains <PID> [partial]`
Find all paths where a value contains a partial string match.
```bash
pylow jq-locate-value-contains 4821 Kernel
```
```
Paths with values containing "Kernel":
  .modules[2].name = "Kernel Payment Module"
  .description = "Kernel-level trace event"
```

---

### `pylow jq-trace-all-keys <PID> [key]`
Find every occurrence of a key across all nested objects and arrays.
```bash
pylow jq-trace-all-keys 4821 username
```
```
All occurrences of "username":
  .createdBy.username = "gravity_admin"
  .modifiedBy.username = "system"
  .audit[0].username = "gravity_admin"
```

---

### `pylow jq-heavy-objects <PID>`
Identify the heaviest nested objects by field count.
```bash
pylow jq-heavy-objects 4821
```
```
=== HEAVIEST OBJECTS ===
  .actStatus          : 8 fields
  .refLinkTo.payModes : 6 fields
  .createdBy          : 5 fields
```

---

### `pylow jq-repeated-schema <PID>`
Find repeated structural patterns (e.g. audit trails, references) across the document.
```bash
pylow jq-repeated-schema 4821
```
```
Repeated schemas detected:
  Pattern {id, name} appears 6x at:
    .actStatus, .refLinkTo, .createdBy, ...
```

---

### `pylow jq-common-audit <PID>`
Find nested objects that share the same audit trail key set (createdBy, modifiedBy, etc).
```bash
pylow jq-common-audit 4821
```
```
=== AUDIT TRAIL ANALYSIS ===
Objects with common audit keys:
  .actStatus     → createdBy, modifiedBy, createdAt
  .refLinkTo     → createdBy, modifiedBy
```

---

### `pylow jq-schema-evolution <PID>`
Compare schema across paginated response pages to detect structural drift.
```bash
pylow jq-schema-evolution 4821
```
```
=== SCHEMA EVOLUTION (page 1 → page 2) ===
  ADDED   : .newField
  REMOVED : .deprecatedFlag
  STABLE  : 44 fields unchanged
```

---

### `pylow jq-validate-fields <PID>`
Assert that mandatory fields are present and non-null.
```bash
pylow jq-validate-fields 4821
```
```
=== FIELD VALIDATION ===
  ✓ id           present
  ✓ actStatus    present
  ✗ paymentRef   MISSING
  ✗ enddate      NULL
  Result: 2 violations
```

---

### `pylow jq-watch-changes <PID>`
Snapshot responses over time and track which fields change between calls.
```bash
pylow jq-watch-changes 4821
```
```
=== Snapshot 1 → Snapshot 2 ===
  CHANGED: .actStatus.name  PENDING → COMPLETED
  CHANGED: .modifiedAt      2026-06-10T10:00Z → 2026-06-10T10:05Z
  STABLE : 45 fields
```

---

## CATEGORY 8 — DAG Execution Engine

Run arbitrary step graphs with proper dependency resolution, cycle detection, and level-by-level parallel execution.

### DAG Spec Format
```
"step_name:dep1,dep2  step2:dep1  step3:"
```
- Each node: `name:comma-separated-deps`
- No deps: `auth:` or just `auth`
- Spaces separate nodes

### `pylow dag-dry-run --dag "<spec>" [--dag-file <path>] [--workers <n>]`
Validate DAG — resolve levels, detect cycles. No execution.
```bash
pylow dag-dry-run --dag "auth: get_user:auth get_catalog:auth create_order:get_user,get_catalog"
```
```
=== DAG EXECUTION ENGINE ===
  Steps     : 4
  Levels    : 3
  Workers   : 4
  Mode      : DRY RUN

  Level 0  [auth]
  Level 1  [get_user, get_catalog]
  Level 2  [create_order]

✓ DAG is valid. No cycles. Dry-run complete.
```

Cycle detection:
```bash
pylow dag-dry-run --dag "a:b b:a"
# [dag-engine] CYCLE DETECTED — aborting.
```

---

### `pylow dag-run --dag "<spec>" [--dag-file <path>] [--workers <n>]`
Execute the DAG. Runs each level in parallel (up to `--workers` at a time). Stops at first failed level.
```bash
pylow dag-run --dag "auth: get_user:auth get_catalog:auth create_order:get_user,get_catalog" --workers 4
```
```
=== DAG EXECUTION ENGINE ===
  Steps     : 4
  Levels    : 3
  Workers   : 4
  Mode      : EXECUTE

  Level 0  [auth]
  Level 1  [get_user, get_catalog]
  Level 2  [create_order]

▶ Level 0: ['auth']
  ✓ auth                  51.2ms

▶ Level 1: ['get_user', 'get_catalog']
  ✓ get_user              50.8ms
  ✓ get_catalog           51.1ms

▶ Level 2: ['create_order']
  ✓ create_order          50.9ms

✓ All 4 steps completed in 153.8ms
```

Load from a JSON file:
```bash
# dag.json
{
  "auth": [],
  "get_user": ["auth"],
  "get_catalog": ["auth"],
  "create_order": ["get_user", "get_catalog"]
}

pylow dag-run --dag-file dag.json --workers 8
```

---

### `pylow dag-status`
Show the step-level status of the last DAG run in this session.
```bash
pylow dag-status
```
```
=== DAG STATUS ===
  DONE              auth
  DONE              get_user
  DONE              get_catalog
  DONE              create_order
```

---

## CATEGORY 9 — Saga Orchestrator

Forward/compensate pattern. Steps run in order. On failure, completed steps are rolled back in reverse. Every event is appended to a JSON Lines saga log.

### `pylow saga-run --steps <list> [--fail-at <step>] [--log-file <path>]`
Run forward steps. On failure, compensating transactions execute in reverse for all completed steps.
```bash
# Happy path — all steps commit
pylow saga-run --steps auth,create_order,reserve_inventory,create_payment
```
```
=== SAGA ORCHESTRATOR [saga-1749558821] ===
  Steps    : auth, create_order, reserve_inventory, create_payment
  Log file : /tmp/pylow_saga.log
  Inject   : none

  ▶ Forward  auth                  ✓
  ▶ Forward  create_order          ✓
  ▶ Forward  reserve_inventory     ✓
  ▶ Forward  create_payment        ✓

✓ Saga committed. All 4 steps succeeded.
  Log: /tmp/pylow_saga.log
```

```bash
# Inject failure to test rollback
pylow saga-run --steps auth,create_order,reserve_inventory --fail-at create_order
```
```
=== SAGA ORCHESTRATOR [saga-1749558822] ===
  Steps    : auth, create_order, reserve_inventory
  Inject   : create_order

  ▶ Forward  auth                  ✓
  ▶ Forward  create_order          ✗  FAILED

  Rolling back completed steps...
  ↩ Compensate auth               ✓

✗ Saga rolled back. Failed at: create_order
  Log: /tmp/pylow_saga.log
```

Custom log file:
```bash
pylow saga-run --steps auth,create_order --log-file /var/log/my_saga.log
```

---

### `pylow saga-log [--log-file <path>]`
Display the saga event log with color-coded events.
```bash
pylow saga-log
pylow saga-log --log-file /var/log/my_saga.log
```
```
=== SAGA LOG: /tmp/pylow_saga.log ===

  2026-06-11T06:09:01Z  SAGA_START          — steps=['auth', 'create_order', ...]
  2026-06-11T06:09:01Z  FORWARD_START       [auth]
  2026-06-11T06:09:01Z  FORWARD_OK          [auth]
  2026-06-11T06:09:01Z  FORWARD_START       [create_order]
  2026-06-11T06:09:01Z  FORWARD_OK          [create_order]
  2026-06-11T06:09:02Z  SAGA_COMMITTED      — all_steps=['auth', 'create_order']
```

Event color key:
| Event | Color |
|---|---|
| `SAGA_START` / `SAGA_COMMITTED` | Cyan / Green |
| `FORWARD_START` | Yellow |
| `FORWARD_OK` | Green |
| `FORWARD_FAIL` | Red |
| `COMPENSATE_START` / `COMPENSATE_OK` | Magenta / Green |
| `SAGA_ROLLED_BACK` | Red |

---

### `pylow saga-replay [--log-file <path>]`
Re-run the steps from a committed saga log (no injected failures).
```bash
pylow saga-replay
pylow saga-replay --log-file /var/log/my_saga.log
```
```
[saga-replay] Replaying 4 steps from /tmp/pylow_saga.log

=== SAGA ORCHESTRATOR [saga-1749558900] ===
  ▶ Forward  auth                  ✓
  ▶ Forward  create_order          ✓
  ▶ Forward  reserve_inventory     ✓
  ▶ Forward  create_payment        ✓

✓ Saga committed. All 4 steps succeeded.
  Log: /tmp/pylow_saga.log.replay
```

---

## Diagnostic Decision Tree

Run `pylow triage <PID>` first. Read the output and go to the right command:

```
cpu_samples high + offcpu low   → pylow cpu-bound <PID>
cpu_samples low  + offcpu high  → pylow io-bound <PID>
syscalls very high              → pylow syscall-storm <PID>
page_faults high                → pylow page-faults <PID>
all counts low                  → pylow deadlock <PID>
```

### Full Drill-Down by Symptom

| Symptom | First Command | Drill-Down |
|---|---|---|
| App is slow | `triage` | → `cpu-bound` or `io-bound` |
| Memory growing | `malloc` | → `pyleak` |
| Random crashes | `pyexcept` | → `anomaly-trigger` |
| Process hangs | `deadlock` | → `kernel-blocked` |
| Too many syscalls | `syscall-storm` | → `syscall` |
| Wrong output / logic | `ordered-log` | → `intercept` → `jq-structural-diff` |
| Multi-service slowdown | `service-map` | → `correlation` |
| Unknown JSON schema | `jq-schema` | → `jq-nulls` → `jq-validate-fields` |
| API HTTP issue | `curl-perf` | → `jwt-decode` or `cert-check` |
| Distributed workflow | `dag-dry-run` | → `dag-run` |
| Rollback on failure | `saga-run` | → `saga-log` |

---

## bpftrace Prerequisites

The kernel tracing commands (`syscall`, `malloc`, `tcp`, `io`, `flame`, `sched`, `page-faults`, `context-switches`, `kernel-blocked`, `tlb-shootdowns`, `irq-impact`, `pycall`, `pyframe`, `pycpu`, `pyexcept`, `pyiowait`, `pygil`, `pyleak`, `pyreq`, `pythread`, `pyasync`, `pyargs`, `pysyscall`, `pynplus1`, `pygraph`, `pyanomaly`, `pydash`, `pysingle`, `timeline`, `triage`, `cpu-bound`, `io-bound`, `syscall-storm`, `deadlock`, `service-map`, `ordered-log`, `intercept`, `anomaly-trigger`, `correlation`) require bpftrace on the host.

Install bpftrace:
```bash
# Ubuntu / Debian
sudo apt-get install bpftrace

# Fedora / RHEL
sudo dnf install bpftrace
```

USDT Python probes require a debug-enabled Python build:
```bash
python3 -c "import sys; print(sys.version)"
# Should show: with DTrace support
# Or check: readelf -n /usr/bin/python3 | grep stapsdt
```

Commands that do **not** require bpftrace (pure Python):
`attach`, `flow`, `stitch`, `slow`, `diff`, `pyanomaly`, `pydash`, `jq-*`, `curl-perf`, `jwt-decode`, `cert-check`, `rate-limit-test`, `parallel-fetch`, `jq-search`, `awk-stats`, `tee-branch`, `pipe-decouple`, `sed-mask`, `dag-run`, `dag-dry-run`, `dag-status`, `saga-run`, `saga-log`, `saga-replay`

---

## Command Quick Reference

```bash
# ── CORE ──────────────────────────────────────────────────────
pylow attach <PID>
pylow flow --last
pylow stitch --services api,worker,ml-service
pylow slow --threshold 200ms --watch
pylow diff --before v1.2 --after v1.3

# ── KERNEL & SYSCALL ──────────────────────────────────────────
pylow syscall <PID>
pylow malloc <PID>
pylow tcp <PID>
pylow io <PID>
pylow flame <PID> --duration 5
pylow sched <PID>
pylow page-faults <PID>
pylow context-switches <PID>
pylow kernel-blocked <PID>
pylow tlb-shootdowns <PID>
pylow irq-impact <PID>

# ── PYTHON RUNTIME ────────────────────────────────────────────
pylow pycall <PID>
pylow pyframe <PID>
pylow pycpu <PID>
pylow pyexcept <PID>
pylow pyiowait <PID>
pylow pygil <PID>
pylow pyleak <PID>
pylow pyreq <PID>
pylow timeline <PID> --duration 5.0
pylow pythread <PID>
pylow pyasync <PID>
pylow pyargs <PID>
pylow pysyscall <PID>
pylow pynplus1 <PID>
pylow pygraph <PID>
pylow pyanomaly <PID>
pylow pydash <PID>
pylow pysingle <PID> handle_request

# ── DIAGNOSTIC WORKFLOWS ──────────────────────────────────────
pylow triage <PID>
pylow cpu-bound <PID>
pylow io-bound <PID>
pylow syscall-storm <PID>
pylow deadlock <PID>
pylow service-map <PID>
pylow ordered-log <PID> --filter-internals
pylow intercept <PID> process_payment
pylow anomaly-trigger <PID> validate_payment
pylow correlation <PID> api-gateway

# ── HTTP & API ────────────────────────────────────────────────
pylow curl-perf <PID> https://api.example.com/endpoint
pylow jwt-decode <PID>
pylow cert-check <PID> api.example.com
pylow rate-limit-test <PID>
pylow parallel-fetch <PID> --concurrency 8

# ── PIPELINE PATTERNS ─────────────────────────────────────────
pylow jq-search <PID> error
pylow awk-stats <PID>
pylow tee-branch <PID>
pylow pipe-decouple <PID> /tmp/payment_pipe
pylow sed-mask <PID>

# ── JSON ANALYSIS ─────────────────────────────────────────────
pylow jq-schema <PID>
pylow jq-nulls <PID>
pylow jq-null-paths <PID>
pylow jq-locate-key <PID> salesActivities
pylow jq-key-path <PID> name
pylow jq-all-keys <PID>
pylow jq-leaf-paths <PID> --filter-val COMPLETED
pylow jq-clean-nulls <PID>
pylow jq-depth-map <PID>
pylow jq-type-map <PID>
pylow jq-find-value <PID> gravity_admin
pylow jq-structural-diff <PID>
pylow jq-extract-subtree <PID> appModulesId
pylow jq-summary <PID>
pylow jq-validate-schema <PID> schema.json
pylow jq-array-schema <PID>
pylow jq-null-pct <PID>
pylow jq-non-null-leaves <PID>
pylow jq-parent-context <PID> salesActivities
pylow jq-locate-value-contains <PID> Kernel
pylow jq-trace-all-keys <PID> username
pylow jq-heavy-objects <PID>
pylow jq-repeated-schema <PID>
pylow jq-common-audit <PID>
pylow jq-schema-evolution <PID>
pylow jq-validate-fields <PID>
pylow jq-watch-changes <PID>

# ── DAG ENGINE ────────────────────────────────────────────────
pylow dag-dry-run --dag "auth: get_user:auth get_catalog:auth create_order:get_user,get_catalog"
pylow dag-run --dag "auth: get_user:auth get_catalog:auth create_order:get_user,get_catalog" --workers 4
pylow dag-run --dag-file dag.json
pylow dag-status

# ── SAGA ORCHESTRATOR ─────────────────────────────────────────
pylow saga-run --steps auth,create_order,reserve_inventory,create_payment
pylow saga-run --steps auth,create_order --fail-at create_order
pylow saga-log
pylow saga-log --log-file /var/log/my_saga.log
pylow saga-replay
pylow saga-replay --log-file /var/log/my_saga.log

# ── PROTOCOL & ADVANCED PIPELINE CONTROL ───────────────────────
pylow net-tcp <PID> --url https://api.example.com
pylow chaos-run --url https://api.example.com/payments --rate 30
pylow contract-test <PID> --contract /path/to/contract.json
pylow rate-limit-check <PID> --headers-file /tmp/headers.txt
pylow shadow-compare --prod-file /tmp/prod.json --staging-file /tmp/staging.json
pylow load-gen --url https://api.example.com/payments --rps 20 --duration 10
pylow webhook-mock --port 9000 --secret whsec_secretkey
pylow behavior-fingerprint --url https://api.example.com/payments
pylow mtls-diagnose --cert /tmp/client.crt --key /tmp/client.key
pylow grpc-proto --method PaymentsService/GetPayment --payload '{"id": 462}'
pylow graphql-nplus1 --url https://api.example.com/graphql
pylow ws-handshake --url wss://api.example.com/ws
pylow infra-fingerprint --url https://api.example.com/payments
pylow diff-fuzz --url-a https://api-v1.example.com --url-b https://api-v2.example.com
```

---

### `pylow mtls-diagnose`
Verify mutual TLS configuration, certificate chains validity and pin server certificates.
```bash
pylow mtls-diagnose --cert /tmp/client.crt --key /tmp/client.key
```

---

### `pylow grpc-proto`
Encode protobuf structures to gRPC 5-byte frame binary formats and analyze status trailers.
```bash
pylow grpc-proto --method PaymentsService/GetPayment --payload '{"id": 462}'
```

---

### `pylow graphql-nplus1`
Audit GraphQL schemas for N+1 database round-trip loop overheads and depth limits checks.
```bash
pylow graphql-nplus1 --url https://api.example.com/graphql
```

---

### `pylow ws-handshake`
Verify WebSocket protocol upgrades and handshake connection status.
```bash
pylow ws-handshake --url wss://api.example.com/ws
```

---

### `pylow infra-fingerprint`
Probe reverse proxy paths, CDN edge caching latency, and WAF rulesets.
```bash
pylow infra-fingerprint --url https://api.example.com/payments
```

---

### `pylow diff-fuzz`
Execute differential fuzz testing between two API versions using prototype pollution and boundary payloads.
```bash
pylow diff-fuzz --url-a https://api-v1.example.com --url-b https://api-v2.example.com
```

