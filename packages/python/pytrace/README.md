


# pytrace

One CLI. Zero code changes. Full system flow visibility for any Python service or distributed system.

## How it works under the hood
Three layers working together:
- **Layer 1** → OTel auto-instrumentation (HTTP, DB, gRPC, queues — zero code changes)
- **Layer 2** → bpftrace USDT (Python function call tree, syscalls)
- **Layer 3** → pytrace CLI (stitches both, renders the flow)

---

## Complete CLI Command Reference & Outputs

Here is the usage documentation and sample outputs for every command in the `pytrace` tool:

### 1. `pytrace attach <pid>`
Attach to any running Python process and start collecting trace logs immediately.
```bash
pytrace attach 4821
```
**Output:**
```text
✓ Attached to process 4821. Monitoring execution events...
```

### 2. `pytrace flow`
Renders the complete execution flow tree (local/distributed spans & events) from the trace repository.
```bash
pytrace flow --last
```
**Output:**
```text
handle_request 450ms
├── authenticate_user 20ms
│   └── [redis GET session_id] 15ms
└── call_llm_chain 410ms
    └── [POST api.openai.com/v1/chat/completions] 400ms
        └── waiting (epoll_wait) 390ms   ← bottleneck
```

### 3. `pytrace stitch`
Stitch distributed traces together across service boundaries using traceparent headers.
```bash
pytrace stitch --services api,worker,ml-service
```
**Output:**
```text
REQUEST trace-id: t_demo_flow_123

  api-gateway          450ms  handle_request
  └── api-gateway          20ms  authenticate_user
      └── api-gateway          15ms  redis GET session_id
  └── api-gateway          410ms  call_llm_chain
      └── api-gateway          400ms  POST api.openai.com/v1/chat/completions
          └── api-gateway          390ms  waiting (epoll_wait)
```

### 4. `pytrace slow`
Continuously daemonize/monitor and surface slow execution paths exceeding a latency threshold.
```bash
pytrace slow --threshold 200ms --watch
```
**Output:**
```text
Continuous monitoring daemon started. Threshold: 200ms, Watch: False
SLOW PATHS detected (last 5 min):

  #1  handle_request → call_llm_chain → POST api.openai.com/v1/chat/completions → [waiting (epoll_wait)]
      avg: 390ms  occurrences: 1
      root cause: epoll_wait 310ms — network latency to openai
```

### 5. `pytrace diff`
Compare execution flow metrics between versions or releases to detect regressions.
```bash
pytrace diff --before deploy-v1.2 --after deploy-v1.3
```
**Output:**
```text
Comparing before v1.2 vs after v1.3...

REGRESSIONS:

  handle_request     +150ms avg  (was 200ms, now 350ms)
  call_llm           +140ms avg  (was 180ms, now 320ms)
  serialize          +12ms avg  (was 3ms, now 15ms)

NEW CALLS in v1.3:
  validate_schema    8ms  (added input validation)

REMOVED in v1.3:
  legacy_cache_check (removed)
```

### 6. `pytrace syscall <pid>`
Trace syscall counts and histogram latency patterns for the target process.
```bash
pytrace syscall 4821
```
**Output:**
```text
Attaching syscall counter to PID 4821...
✓ Attached. Monitoring syscall events... Ctrl+C to stop.

--- BPF Map: @sys_counts ---
  sys_enter_read: 231
  sys_enter_write: 184
  sys_enter_epoll_wait: 42
```

### 7. `pytrace malloc <pid>`
Profile allocations and heap sizing metrics.
```bash
pytrace malloc 4821
```
**Output:**
```text
Attaching allocator profile to PID 4821...
✓ Attached. Monitoring memory allocations... Ctrl+C to stop.

--- BPF Map: @alloc_sizes (bytes allocated) ---
[64, 127]              45 |@@@@@@@@@@@                         |
[512, 1023]           120 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
[4096, 8191]           18 |@@@@                                |
```

### 8. `pytrace tcp <pid>`
Trace outbound TCP latency.
```bash
pytrace tcp 4821
```
**Output:**
```text
Attaching TCP latency tracer to PID 4821...
✓ Attached. Monitoring TCP sendmsg... Ctrl+C to stop.

--- BPF Map: @tcp_send_us (ns delay) ---
[100000, 200000]       21 |@@@@@@@@@@                          |
```

### 9. `pytrace io <pid>`
Trace Block and File I/O read/write latencies.
```bash
pytrace io 4821
```
**Output:**
```text
Attaching File I/O latency tracer to PID 4821...
✓ Attached. Collecting block I/O events... Ctrl+C to stop.

--- BPF Map: @read_lat (ns) ---
[4096, 8191]          150 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
[16384, 32767]        23 |@@@@@                               |
```

### 10. `pytrace flame <pid>`
Generate sampling-based user/kernel stack flame graphs.
```bash
pytrace flame 4821 --duration 5
```
**Output:**
```text
Attaching kernel profile sampler to PID 4821 for 5s...
✓ Attached. Sampling for 5s...
✓ Saved flame graph to flamegraph.svg
```

### 11. `pytrace sched <pid>`
Monitor runqueue latency and scheduling delays.
```bash
pytrace sched 4821
```
**Output:**
```text
Attaching scheduler delay tracer to PID 4821...
✓ Attached. Collecting scheduler runqueue events... Ctrl+C to stop.

--- BPF Map: @runq_latency_us (us delay) ---
[1, 2]                 98 |@@@@@@@@@@@@@@@@@@@@@@@@            |
[4, 8]                142 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
```

### 12. `pytrace pycall <pid>`
Profile Python `PyObject_Call` execution timings.
```bash
pytrace pycall 4821
```
**Output:**
```text
Attaching Python function call timer to PID 4821...
✓ Attached. Collecting PyObject_Call events... Ctrl+C to stop.

--- BPF Map: @latency (time spent per function in us) ---
SLOW execute_query took 12400us
SLOW process_job took 1850us
```

### 13. `pytrace pyframe <pid>`
Log Python execution contexts at the frame level (file, function, line).
```bash
pytrace pyframe 4821
```
**Output:**
```text
Attaching Python frame USDT tracer to PID 4821...
✓ Attached. Collecting USDT frame events... Ctrl+C to stop.

ENTER execute_query() @ db/models.py:142
slow_query() @ db/models.py:142 — p99: 340ms
```

### 14. `pytrace pycpu <pid>`
Identify CPU hotspots in Python runtime execution stacks.
```bash
pytrace pycpu 4821
```
**Output:**
```text
Attaching CPU hotspot sampler to PID 4821...
✓ Attached. Sampling CPU stacks... Ctrl+C to stop.

--- BPF Map: @stacks ---
  [0x7f3b821034bc, 0x7f3b821035dc]: 145
  -> Resolved: call_llm_chain @ gateway/orchestrator.py:120
```

### 15. `pytrace pyexcept <pid>`
Trace raised and caught exceptions within Python virtual machine.
```bash
pytrace pyexcept 4821
```
**Output:**
```text
Attaching Python exception tracer to PID 4821...
✓ Attached. Monitoring exceptions... Ctrl+C to stop.

EXCEPTION KeyError @ tid=10234
  [ustack]:
    get_user_context @ db/client.py:48
```

### 16. `pytrace pyiowait <pid>`
Trace Python code blocked waiting on blocking I/O calls.
```bash
pytrace pyiowait 4821
```
**Output:**
```text
Attaching I/O Wait blocking call tracer to PID 4821...
✓ Attached. Monitoring blocking sys_read calls... Ctrl+C to stop.

BLOCKING READ 12ms
  [ustack]:
    fetch_metadata @ db/client.py:54
```

### 17. `pytrace pygil <pid>`
Profile GIL lock acquisition delays and thread contention.
```bash
pytrace pygil 4821
```
**Output:**
```text
Attaching GIL lock contention tracer to PID 4821...
✓ Attached. Monitoring GIL wait states... Ctrl+C to stop.

GIL WAIT 1250us tid=10234 stack:
  [ustack]:
    calculate_features @ ml/engine.py:89
```

### 18. `pytrace pyleak <pid>`
Profile heap allocations to detect memory leak patterns.
```bash
pytrace pyleak 4821
```
**Output:**
```text
Attaching memory leak tracer to PID 4821...
✓ Attached. Collecting memory allocation metrics... Ctrl+C to stop.

=== TOP ALLOCATORS ===
@allocs[0x7f3b821034bc]: 10485760 bytes
  -> allocating callsite: load_dataset @ ml/data.py:12
```

### 19. `pytrace pyreq <pid>`
Measure end-to-end request lifecycle breakdown.
```bash
pytrace pyreq 4821
```
**Output:**
```text
Attaching Request Lifecycle timer to PID 4821...
✓ Attached. Collecting Request Latency counts... Ctrl+C to stop.

REQ START tid=10234
REQ DONE total=340ms db=310ms other=30ms
```

### 20. `pytrace timeline <pid>`
Trace absolute chronological timeline call graph.
```bash
pytrace timeline 4821 --duration 5.0 --threshold 2.0
```
**Output:**
```text
[     0.000ms] → handle_request()  server.py:45
[     0.040ms]   → parse_headers()  http.py:12
[     0.051ms]   ← parse_headers()  [0.011ms]
[     0.055ms]   → execute_query()  db.py:88
[    91.230ms]   ← execute_query()  [91.175ms]  ⚠️ SLOW
```

### 21. `pytrace pythread <pid>`
Trace thread-aware function call timelines with self-time.
```bash
pytrace pythread 4821
```
**Output:**
```text
Attaching thread-aware tracer to PID 4821...
✓ Attached. Collecting threaded events... Ctrl+C to stop.

--- Thread ID: 10001 ---
  parse_headers() spent 0.00ms (Self time: 0.00ms)
```

### 22. `pytrace pyasync <pid>`
Trace async await coroutine metrics and yields.
```bash
pytrace pyasync 4821
```
**Output:**
```text
Attaching async/coroutine tracer to PID 4821...
✓ Attached. Monitoring coroutine suspends/resumes... Ctrl+C to stop.

--- Coroutine: 0x7f3b821034bc ---
  Suspended counts: 2
  Total CPU Time: 80us
```

### 23. `pytrace pyargs <pid>`
Profile Python function call argument types and layout.
```bash
pytrace pyargs 4821
```
**Output:**
```text
Attaching argument Layout layout-tracer to PID 4821...
✓ Attached. Dereferencing Python structs... Ctrl+C to stop.

1000 CALL obj=0x7f3b821034bc args=0x7f3b821051fa
```

### 24. `pytrace pysyscall <pid>`
Profile syscalls attributed directly to Python frames.
```bash
pytrace pysyscall 4821
```
**Output:**
```text
Attaching syscall-to-Python attribution tracer to PID 4821...
✓ Attached. Monitoring slow read and futex syscalls... Ctrl+C to stop.

=== SLOW READ fd=4 dur=12ms ===
  [ustack]:
    fetch_metadata @ db/client.py:54
```

### 25. `pytrace pynplus1 <pid>`
Detect potential ORM loop-driven N+1 query patterns.
```bash
pytrace pynplus1 4821
```
**Output:**
```text
Attaching N+1 query loop detector to PID 4821...
✓ Attached. Monitoring ORM execute loops... Ctrl+C to stop.

⚠️  N+1 CANDIDATE: db/models.py:142
   Called 15x in 5s (3.0/s)
```

### 26. `pytrace pygraph <pid>`
Trace hierarchical call relationships.
```bash
pytrace pygraph 4821
```
**Output:**
```text
handle_request()  calls=1  avg=0.00ms  (server.py:45)
  execute_query()  calls=1  avg=0.00ms  (db.py:88)
```

### 27. `pytrace pyanomaly <pid>`
Identify slow function calls using statistical baselines.
```bash
pytrace pyanomaly 4821
```
**Output:**
```text
[BASELINE] execute_query(): mean=10.33ms stddev=0.76ms
🚨 ANOMALY execute_query(): 45.00ms vs baseline 10.33ms
```

### 28. `pytrace pydash <pid>`
Stream traces directly to live curses dashboard.
```bash
pytrace pydash 4821
```
**Output:**
```text
Attaching curses dashboard to PID 4821...
=== LIVE FUNCTION TRACER ===
RECENT CALLS:
  handle_request() 120.40ms
```

### 29. `pytrace pysingle <pid> <target_func>`
Trace single request / execution call tree with self time.
```bash
pytrace pysingle 4821 handle_request
```
**Output:**
```text
[     0.000ms] → handle_request()  server.py:45
[     0.011ms]   → validate_token()  auth.py:12
[     0.015ms]   ← validate_token()  total=0.004ms  self=0.003ms
```
