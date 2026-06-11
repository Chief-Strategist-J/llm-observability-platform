


# pylow

One CLI. Zero code changes. Full system flow visibility for any Python service or distributed system.

## Installation & Setup

You can install `pylow` globally via pip:
```bash
pip install pylow
```

> [!IMPORTANT]
> If you get `Command 'pylow' not found` after installation, make sure Python's user bin directory is in your `PATH`.
> Run the following commands to add it to your profile:
> ```bash
> echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
> source ~/.bashrc
> ```

## How it works under the hood
Three layers working together:
- **Layer 1** → OTel auto-instrumentation (HTTP, DB, gRPC, queues — zero code changes)
- **Layer 2** → bpftrace USDT (Python function call tree, syscalls)
- **Layer 3** → pylow CLI (stitches both, renders the flow)

---

## Complete CLI Command Reference & Outputs

Here is the usage documentation and sample outputs for every command in the `pylow` tool:

### 1. `pylow attach <pid>`
Attach to any running Python process and start collecting trace logs immediately.
```bash
pylow attach 4821
```
**Output:**
```text
✓ Attached to process 4821. Monitoring execution events...
```

### 2. `pylow flow`
Renders the complete execution flow tree (local/distributed spans & events) from the trace repository.
```bash
pylow flow --last
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

### 3. `pylow stitch`
Stitch distributed traces together across service boundaries using traceparent headers.
```bash
pylow stitch --services api,worker,ml-service
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

### 4. `pylow slow`
Continuously daemonize/monitor and surface slow execution paths exceeding a latency threshold.
```bash
pylow slow --threshold 200ms --watch
```
**Output:**
```text
Continuous monitoring daemon started. Threshold: 200ms, Watch: False
SLOW PATHS detected (last 5 min):

  #1  handle_request → call_llm_chain → POST api.openai.com/v1/chat/completions → [waiting (epoll_wait)]
      avg: 390ms  occurrences: 1
      root cause: epoll_wait 310ms — network latency to openai
```

### 5. `pylow diff`
Compare execution flow metrics between versions or releases to detect regressions.
```bash
pylow diff --before deploy-v1.2 --after deploy-v1.3
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

### 6. `pylow syscall <pid>`
Trace syscall counts and histogram latency patterns for the target process.
```bash
pylow syscall 4821
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

### 7. `pylow malloc <pid>`
Profile allocations and heap sizing metrics.
```bash
pylow malloc 4821
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

### 8. `pylow tcp <pid>`
Trace outbound TCP latency.
```bash
pylow tcp 4821
```
**Output:**
```text
Attaching TCP latency tracer to PID 4821...
✓ Attached. Monitoring TCP sendmsg... Ctrl+C to stop.

--- BPF Map: @tcp_send_us (ns delay) ---
[100000, 200000]       21 |@@@@@@@@@@                          |
```

### 9. `pylow io <pid>`
Trace Block and File I/O read/write latencies.
```bash
pylow io 4821
```
**Output:**
```text
Attaching File I/O latency tracer to PID 4821...
✓ Attached. Collecting block I/O events... Ctrl+C to stop.

--- BPF Map: @read_lat (ns) ---
[4096, 8191]          150 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
[16384, 32767]        23 |@@@@@                               |
```

### 10. `pylow flame <pid>`
Generate sampling-based user/kernel stack flame graphs.
```bash
pylow flame 4821 --duration 5
```
**Output:**
```text
Attaching kernel profile sampler to PID 4821 for 5s...
✓ Attached. Sampling for 5s...
✓ Saved flame graph to flamegraph.svg
```

### 11. `pylow sched <pid>`
Monitor runqueue latency and scheduling delays.
```bash
pylow sched 4821
```
**Output:**
```text
Attaching scheduler delay tracer to PID 4821...
✓ Attached. Collecting scheduler runqueue events... Ctrl+C to stop.

--- BPF Map: @runq_latency_us (us delay) ---
[1, 2]                 98 |@@@@@@@@@@@@@@@@@@@@@@@@            |
[4, 8]                142 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
```

### 12. `pylow pycall <pid>`
Profile Python `PyObject_Call` execution timings.
```bash
pylow pycall 4821
```
**Output:**
```text
Attaching Python function call timer to PID 4821...
✓ Attached. Collecting PyObject_Call events... Ctrl+C to stop.

--- BPF Map: @latency (time spent per function in us) ---
SLOW execute_query took 12400us
SLOW process_job took 1850us
```

### 13. `pylow pyframe <pid>`
Log Python execution contexts at the frame level (file, function, line).
```bash
pylow pyframe 4821
```
**Output:**
```text
Attaching Python frame USDT tracer to PID 4821...
✓ Attached. Collecting USDT frame events... Ctrl+C to stop.

ENTER execute_query() @ db/models.py:142
slow_query() @ db/models.py:142 — p99: 340ms
```

### 14. `pylow pycpu <pid>`
Identify CPU hotspots in Python runtime execution stacks.
```bash
pylow pycpu 4821
```
**Output:**
```text
Attaching CPU hotspot sampler to PID 4821...
✓ Attached. Sampling CPU stacks... Ctrl+C to stop.

--- BPF Map: @stacks ---
  [0x7f3b821034bc, 0x7f3b821035dc]: 145
  -> Resolved: call_llm_chain @ gateway/orchestrator.py:120
```

### 15. `pylow pyexcept <pid>`
Trace raised and caught exceptions within Python virtual machine.
```bash
pylow pyexcept 4821
```
**Output:**
```text
Attaching Python exception tracer to PID 4821...
✓ Attached. Monitoring exceptions... Ctrl+C to stop.

EXCEPTION KeyError @ tid=10234
  [ustack]:
    get_user_context @ db/client.py:48
```

### 16. `pylow pyiowait <pid>`
Trace Python code blocked waiting on blocking I/O calls.
```bash
pylow pyiowait 4821
```
**Output:**
```text
Attaching I/O Wait blocking call tracer to PID 4821...
✓ Attached. Monitoring blocking sys_read calls... Ctrl+C to stop.

BLOCKING READ 12ms
  [ustack]:
    fetch_metadata @ db/client.py:54
```

### 17. `pylow pygil <pid>`
Profile GIL lock acquisition delays and thread contention.
```bash
pylow pygil 4821
```
**Output:**
```text
Attaching GIL lock contention tracer to PID 4821...
✓ Attached. Monitoring GIL wait states... Ctrl+C to stop.

GIL WAIT 1250us tid=10234 stack:
  [ustack]:
    calculate_features @ ml/engine.py:89
```

### 18. `pylow pyleak <pid>`
Profile heap allocations to detect memory leak patterns.
```bash
pylow pyleak 4821
```
**Output:**
```text
Attaching memory leak tracer to PID 4821...
✓ Attached. Collecting memory allocation metrics... Ctrl+C to stop.

=== TOP ALLOCATORS ===
@allocs[0x7f3b821034bc]: 10485760 bytes
  -> allocating callsite: load_dataset @ ml/data.py:12
```

### 19. `pylow pyreq <pid>`
Measure end-to-end request lifecycle breakdown.
```bash
pylow pyreq 4821
```
**Output:**
```text
Attaching Request Lifecycle timer to PID 4821...
✓ Attached. Collecting Request Latency counts... Ctrl+C to stop.

REQ START tid=10234
REQ DONE total=340ms db=310ms other=30ms
```

### 20. `pylow timeline <pid>`
Trace absolute chronological timeline call graph.
```bash
pylow timeline 4821 --duration 5.0 --threshold 2.0
```
**Output:**
```text
[     0.000ms] → handle_request()  server.py:45
[     0.040ms]   → parse_headers()  http.py:12
[     0.051ms]   ← parse_headers()  [0.011ms]
[     0.055ms]   → execute_query()  db.py:88
[    91.230ms]   ← execute_query()  [91.175ms]  ⚠️ SLOW
```

### 21. `pylow pythread <pid>`
Trace thread-aware function call timelines with self-time.
```bash
pylow pythread 4821
```
**Output:**
```text
Attaching thread-aware tracer to PID 4821...
✓ Attached. Collecting threaded events... Ctrl+C to stop.

--- Thread ID: 10001 ---
  parse_headers() spent 0.00ms (Self time: 0.00ms)
```

### 22. `pylow pyasync <pid>`
Trace async await coroutine metrics and yields.
```bash
pylow pyasync 4821
```
**Output:**
```text
Attaching async/coroutine tracer to PID 4821...
✓ Attached. Monitoring coroutine suspends/resumes... Ctrl+C to stop.

--- Coroutine: 0x7f3b821034bc ---
  Suspended counts: 2
  Total CPU Time: 80us
```

### 23. `pylow pyargs <pid>`
Profile Python function call argument types and layout.
```bash
pylow pyargs 4821
```
**Output:**
```text
Attaching argument Layout layout-tracer to PID 4821...
✓ Attached. Dereferencing Python structs... Ctrl+C to stop.

1000 CALL obj=0x7f3b821034bc args=0x7f3b821051fa
```

### 24. `pylow pysyscall <pid>`
Profile syscalls attributed directly to Python frames.
```bash
pylow pysyscall 4821
```
**Output:**
```text
Attaching syscall-to-Python attribution tracer to PID 4821...
✓ Attached. Monitoring slow read and futex syscalls... Ctrl+C to stop.

=== SLOW READ fd=4 dur=12ms ===
  [ustack]:
    fetch_metadata @ db/client.py:54
```

### 25. `pylow pynplus1 <pid>`
Detect potential ORM loop-driven N+1 query patterns.
```bash
pylow pynplus1 4821
```
**Output:**
```text
Attaching N+1 query loop detector to PID 4821...
✓ Attached. Monitoring ORM execute loops... Ctrl+C to stop.

⚠️  N+1 CANDIDATE: db/models.py:142
   Called 15x in 5s (3.0/s)
```

### 26. `pylow pygraph <pid>`
Trace hierarchical call relationships.
```bash
pylow pygraph 4821
```
**Output:**
```text
handle_request()  calls=1  avg=0.00ms  (server.py:45)
  execute_query()  calls=1  avg=0.00ms  (db.py:88)
```

### 27. `pylow pyanomaly <pid>`
Identify slow function calls using statistical baselines.
```bash
pylow pyanomaly 4821
```
**Output:**
```text
[BASELINE] execute_query(): mean=10.33ms stddev=0.76ms
🚨 ANOMALY execute_query(): 45.00ms vs baseline 10.33ms
```

### 28. `pylow pydash <pid>`
Stream traces directly to live curses dashboard.
```bash
pylow pydash 4821
```
**Output:**
```text
Attaching curses dashboard to PID 4821...
=== LIVE FUNCTION TRACER ===
RECENT CALLS:
  handle_request() 120.40ms
```

### 29. `pylow pysingle <pid> <target_func>`
Trace single request / execution call tree with self time.
```bash
pylow pysingle 4821 handle_request
```
**Output:**
```text
[     0.000ms] → handle_request()  server.py:45
[     0.011ms]   → validate_token()  auth.py:12
[     0.015ms]   ← validate_token()  total=0.004ms  self=0.003ms
```

### 30. `pylow page-faults <pid>`
Trace page fault hotspots to identify cold memory access patterns.
```bash
pylow page-faults 4821
```
**Output:**
```text
Attaching page faults tracer to PID 4821...
✓ Attached. Collecting page fault events... Ctrl+C to stop.

=== PAGE FAULT HOTSPOTS ===
@faults[
    malloc+0x24
    PyBytes_FromStringAndSize+0x18
    load_dataset @ ml/data.py:12
]: 421
```

### 31. `pylow context-switches <pid>`
Profile preemption context switches and voluntary/involuntary off-CPU delays.
```bash
pylow context-switches 4821
```
**Output:**
```text
Attaching context switches tracer to PID 4821...
✓ Attached. Collecting context switch events... Ctrl+C to stop.

OFF CPU 87ms next_cpu=2

--- BPF Map: @off_cpu_ms ---
[0, 1]                12 |@@@@                                |
[2, 4]                89 |@@@@@@@@@@@@@@                      |
[64, 128]            210 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
```

### 32. `pylow kernel-blocked <pid>`
Trace the exact kernel blocked code path where a process is sleeping in an uninterruptible wait.
```bash
pylow kernel-blocked 4821
```
**Output:**
```text
Attaching kernel blocked stack tracer to PID 4821...
✓ Attached. Monitoring blocked states... Ctrl+C to stop.

BLOCKED IN KERNEL:
        __schedule+0x310
        schedule+0x44
        futex_wait_queue_me+0xb8
        futex_wait+0x120
        do_futex+0x340
        __x64_sys_futex+0x140
        [ustack]:
        pthread_cond_wait+0x12
        take_gil+0x42
        execute_query+0x91  db.py:102
```

### 33. `pylow tlb-shootdowns <pid>`
Profile Translation Lookaside Buffer (TLB) flush rates and reasons.
```bash
pylow tlb-shootdowns 4821
```
**Output:**
```text
Attaching TLB shootdowns tracer to PID 4821...
✓ Attached. Monitoring TLB flushes... Ctrl+C to stop.

--- BPF Map: @tlb_reason ---
[0] (TLB_FLUSH_ON_TASK_SWITCH)              42
[1] (TLB_FLUSH_ON_PAGE_FAULT)              187
```

### 34. `pylow irq-impact <pid>`
Monitor soft and hard IRQ impact vectors to detect when CPU cycles are stolen.
```bash
pylow irq-impact 4821
```
**Output:**
```text
Attaching Soft/Hard IRQ tracer to PID 4821...
✓ Attached. Collecting IRQ impact events... Ctrl+C to stop.

--- BPF Map: @sirq_type ---
[1] (TIMER_SOFTIRQ)                         84
[3] (NET_RX_SOFTIRQ)                        187

--- BPF Map: @sirq_lat (us) ---
[0, 1]                12 |@@@@                                |
[2, 4]                43 |@@@@@@@@@@@@@@                      |
[8, 16]              187 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
```

---

## Diagnostic Decision Tree & Multi-Layer Debugging Workflow

Use this decision tree to diagnose performance degradation layer-by-layer:

```
What are you seeing?
│
├── App is slow
│   │
│   ├── CPU high?
│   │   └── profile:hz:999 + ustack → hottest function
│   │
│   └── CPU normal?
│       └── raw_syscalls timer → which syscall blocking + stack
│
├── Memory growing
│   ├── malloc sum by stack → top allocator
│   └── alloc vs free count → confirm leak
│
├── Random crashes
│   └── raise__exception + ustack → every throw point
│
├── Process hangs
│   ├── sched_switch + ustack → where it sleeps
│   └── PyThread_acquire_lock → deadlock check
│
└── Too much noise from other queries
    └── add /str(arg1) == "your_func"/ filter
        or /str(arg0) == "your_file.py"/
        or /tid == <specific_thread>/
```

### The Mental Model — Layers of Execution

```
Your Python code
      ↓
CPython interpreter (ceval loop)
      ↓
Standard library / third party (SQLAlchemy, requests, asyncio)
      ↓
Python C extensions (.so files)
      ↓
libc (malloc, free, connect, read)
      ↓
System calls (read, write, futex, mmap, connect)
      ↓
Kernel (TCP stack, VFS, scheduler, memory manager)
      ↓
Hardware (CPU, disk, NIC)
```

---

### Step 0 — Quick Triaging (Run first)

Run this for 10 seconds to pinpoint the category of the problem:

```bash
sudo bpftrace -e '
profile:hz:99 /pid == $1/ { @cpu[ustack(perf,3)] = count(); }
tracepoint:sched:sched_switch /args->prev_pid == $1/ { @offcpu = count(); }
tracepoint:raw_syscalls:sys_enter /pid == $1/ { @syscalls = count(); }
software:page-faults:1 /pid == $1/ { @faults = count(); }
interval:s:10 {
  printf("cpu_samples : %d\n", @cpu);
  printf("off_cpu     : %d\n", @offcpu);
  printf("syscalls    : %d\n", @syscalls);
  printf("page_faults : %d\n", @faults);
  exit();
}' <PID>
```

#### Triage Criteria:
* `cpu_samples` high + `offcpu` low &rarr; **CPU BOUND**
* `cpu_samples` low + `offcpu` high &rarr; **I/O BOUND**
* `syscalls` very high &rarr; **SYSCALL STORM**
* `page_faults` high &rarr; **MEMORY**
* All counts low &rarr; **DEADLOCK / STUCK**

---

### CPU BOUND — Your Code Is Burning CPU

#### A. Find exactly which function is hot:
```bash
sudo bpftrace -p <PID> -e '
profile:hz:999 {
  @[ustack(perf, 5)] = count();
}
interval:s:10 {
  print(@, 3);   // top 3 stacks only
  exit();
}'
```

#### B. Confirm with duration:
```bash
sudo bpftrace -p <PID> -e '
usdt:/usr/bin/python3:python:function__entry { @t[tid,str(arg1)] = nsecs; }
usdt:/usr/bin/python3:python:function__return {
  $d = nsecs - @t[tid,str(arg1)];
  if ($d > 10000000) {
    printf("%lldms %s %s:%d\n", $d/1000000, str(arg1), str(arg0), arg2);
  }
  delete(@t[tid,str(arg1)]);
}'
```

---

### I/O BOUND — Your Code Is Waiting

#### A. Find which syscall and Python line caused it:
```bash
sudo bpftrace -e '
tracepoint:raw_syscalls:sys_enter /pid == $1/ {
  @t[tid,args->id] = nsecs;
}
tracepoint:raw_syscalls:sys_exit /pid == $1/ {
  $d = nsecs - @t[tid,args->id];
  if ($d > 5000000) {
    printf("BLOCKED syscall=%d %lldms\n", args->id, $d/1000000);
    print(ustack(perf, 5));
    exit();   // stop after first hit
  }
  delete(@t[tid,args->id]);
}' <PID>
```
*(Translate syscall ID using `ausyscall <ID>`)*

#### B. If it's a read — find which file descriptor:
```bash
sudo bpftrace -e '
tracepoint:syscalls:sys_enter_read /pid == $1/ {
  @t[tid] = nsecs;
  @fd[tid] = args->fd;
}
tracepoint:syscalls:sys_exit_read /pid == $1/ {
  $d = nsecs - @t[tid];
  if ($d > 5000000) {
    printf("SLOW READ fd=%d %lldms\n", @fd[tid], $d/1000000);
    print(ustack(perf,5));
    exit();
  }
  delete(@t[tid]); delete(@fd[tid]);
}' <PID>
```
*(Translate fd to file: `ls -la /proc/<PID>/fd/<FD>`)*

---

### SYSCALL STORM — Too Many Kernel Transitions

#### A. Find which syscall is called most:
```bash
sudo bpftrace -e '
tracepoint:raw_syscalls:sys_enter /pid == $1/ {
  @[args->id] = count();
}
interval:s:5 {
  print(@, 5);   // top 5 syscalls by count
  exit();
}' <PID>
```

#### B. Find which Python code is calling it:
```bash
sudo bpftrace -e '
tracepoint:raw_syscalls:sys_enter /pid == $1 && args->id == <ID>/ {
  @[ustack(perf,5)] = count();
}
interval:s:5 {
  print(@, 3);
  exit();
}' <PID>
```

---

### MEMORY — Growing, Leaking, Slow GC

#### A. Find what is allocating most:
```bash
sudo bpftrace -p <PID> -e '
uprobe:/lib/x86_64-linux-gnu/libc.so.6:malloc {
  @[ustack(perf,5)] = sum(arg0);
}
interval:s:10 {
  print(@, 3);   // top 3 allocating callsites
  exit();
}'
```

#### B. Confirm it's a leak (allocations without frees):
```bash
sudo bpftrace -p <PID> -e '
uprobe:/lib/x86_64-linux-gnu/libc.so.6:malloc {
  @alloc = sum(arg0);
  @alloc_count = count();
}
uprobe:/lib/x86_64-linux-gnu/libc.so.6:free {
  @free_count = count();
}
interval:s:5 {
  printf("allocated: %lldMB  alloc_calls: %d  free_calls: %d\n",
    @alloc/1048576, @alloc_count, @free_count);
  clear(@alloc); clear(@alloc_count); clear(@free_count);
}'
```

#### C. Trace GC pauses:
```bash
sudo bpftrace -p <PID> -e '
usdt:/usr/bin/python3:python:gc__start { @t[tid] = nsecs; @gen[tid] = arg0; }
usdt:/usr/bin/python3:python:gc__done {
  printf("GC gen%d %lldms\n", @gen[tid], (nsecs-@t[tid])/1000000);
}'
```

---

### DEADLOCK / STUCK — Process Is Stuck

#### A. Find where the process is sleeping:
```bash
sudo bpftrace -e '
tracepoint:sched:sched_switch /args->prev_pid == $1/ {
  @stack = ustack(perf, 10);
  @kstack = kstack(perf, 10);
}
interval:s:1 {
  printf("=== WHERE PROCESS SLEEPS ===\n");
  print(@stack);
  print(@kstack);
}' <PID>
```

#### B. Confirm deadlock (lock never released):
```bash
sudo bpftrace -p <PID> -e '
uprobe:/usr/bin/python3:PyThread_acquire_lock {
  @lock[tid, arg0] = nsecs;
}
uprobe:/usr/bin/python3:PyThread_release_lock {
  delete(@lock[tid, arg0]);
}
interval:s:5 {
  printf("=== LOCKS HELD > 5s ===\n");
  print(@lock);
}'
```

---

### Noise Elimination — Surgical Filters

Every diagnostic query can be customized using target filters:

```bash
# Filter by function name
/str(arg1) == "execute_query"/

# Filter by file name
/str(arg0) == "db.py"/

# Filter by thread ID
/tid == 140234/

# Filter by slow execution threshold (e.g. > 50ms)
/nsecs - @t[tid] > 50000000/
```

---

## Logical Error Troubleshooting Playbook (Zero Instrumentation)

When there is no instrumentation and you need to debug logical errors, bpftrace lets you observe execution flows, function arguments, outputs, and cross-service communication payloads directly from the kernel.

### Phase 1 — You Don't Know Which Service Is the Problem (Map Request Flow)

Run this tracepoint probe script on each service PID to find where data flow stops:

```bash
sudo bpftrace -e '
# catch every outbound HTTP call
tracepoint:syscalls:sys_enter_connect /pid == $1/ {
  @conn_start[tid] = nsecs;
  @conn_count = count();
}
tracepoint:syscalls:sys_exit_connect /pid == $1/ {
  if (@conn_start[tid]) {
    $d = nsecs - @conn_start[tid];
    @conn_time = hist($d / 1000000);
    delete(@conn_start[tid]);
  }
}
# catch every inbound request handling
tracepoint:syscalls:sys_enter_accept4 /pid == $1/ {
  @accept_ts = nsecs;
}
tracepoint:syscalls:sys_exit_accept4 /pid == $1/ {
  if (@accept_ts) {
    printf("INBOUND CONNECTION at %lld\n", nsecs);
  }
}
# catch all data sent and received
tracepoint:syscalls:sys_exit_read /pid == $1 && args->ret > 0/ {
  @bytes_in = sum(args->ret);
}
tracepoint:syscalls:sys_exit_write /pid == $1 && args->ret > 0/ {
  @bytes_out = sum(args->ret);
}
interval:s:5 {
  printf("\n=== SERVICE pid=%d ===\n", $1);
  printf("outbound_calls : %d\n", @conn_count);
  printf("bytes_in       : %lld\n", @bytes_in);
  printf("bytes_out      : %lld\n", @bytes_out);
  printf("conn_time_ms:\n"); print(@conn_time);
  clear(@conn_count); clear(@bytes_in);
  clear(@bytes_out); clear(@conn_time);
}' <PID>
```

---

### Phase 2 — You Know Which Service, Not Where Inside (Trace Call Flow)

#### A. Trace every function call and return:
```bash
sudo bpftrace -p <PID> -e '
usdt:/usr/bin/python3:python:function__entry {
  @enter_ts[tid, str(arg1)] = nsecs;
  @call_depth[tid]++;
  printf("%lld %d ENTER %s %s:%d\n",
    nsecs, tid, str(arg1), str(arg0), arg2);
}
usdt:/usr/bin/python3:python:function__return {
  $func = str(arg1);
  $dur  = nsecs - @enter_ts[tid, $func];
  @call_depth[tid]--;
  printf("%lld %d EXIT  %s %lldms\n",
    nsecs, tid, $func, $dur/1000000);
  delete(@enter_ts[tid, $func]);
}'
```

#### B. Narrow execution details to business logic files only:
```bash
sudo bpftrace -p <PID> -e '
usdt:/usr/bin/python3:python:function__entry
/str(arg0) != "<frozen importlib._bootstrap>"
&& str(arg0) != "<frozen importlib._bootstrap_external>"
&& str(arg0) != "threading.py"
&& str(arg0) != "socketserver.py"/ {
  printf("%lld ENTER %-40s %s:%d\n",
    nsecs, str(arg1), str(arg0), arg2);
}
usdt:/usr/bin/python3:python:function__return
/str(arg0) != "<frozen importlib._bootstrap>"
&& str(arg0) != "threading.py"/ {
  printf("%lld EXIT  %s\n", nsecs, str(arg1));
}'
```

---

### Phase 3 — Intercept Data at Boundaries

#### A. Read values being passed to specific functions and trace caller stacks:
```bash
sudo bpftrace -p <PID> -e '
usdt:/usr/bin/python3:python:function__entry
/str(arg1) == "process_payment"/ {
  printf("\n=== process_payment CALLED ===\n");
  printf("file : %s\n", str(arg0));
  printf("line : %d\n", arg2);
  printf("tid  : %d\n", tid);
  printf("time : %lld\n", nsecs);
  print(ustack(perf, 5));
}
usdt:/usr/bin/python3:python:function__return
/str(arg1) == "process_payment"/ {
  printf("=== process_payment RETURNED ===\n");
  printf("duration: %lldms\n", (nsecs - @t[tid])/1000000);
}'
```

#### B. Intercept raw HTTP request/response payloads:
```bash
sudo bpftrace -e '
tracepoint:syscalls:sys_enter_write /pid == $1/ {
  if (args->count > 0 && args->count < 1024) {
    printf("\n=== OUTBOUND DATA ===\n");
    printf("%s\n", str(args->buf, args->count));
    print(ustack(perf, 5));
  }
}
tracepoint:syscalls:sys_enter_read /pid == $1/ {
  @read_buf[tid] = args->buf;
  @read_ts[tid]  = nsecs;
}
tracepoint:syscalls:sys_exit_read /pid == $1 && args->ret > 0/ {
  if (@read_buf[tid] && args->ret < 2048) {
    printf("\n=== INBOUND DATA ===\n");
    printf("RECEIVED: %s\n", str(@read_buf[tid], args->ret));
  }
  delete(@read_buf[tid]);
}' <PID>
```

---

### Phase 4 — Spot Anomaly and Trace Random Failures

#### A. Arm trigger dynamically on anomalies to avoid trace noise:
```bash
sudo bpftrace -p <PID> -e '
usdt:/usr/bin/python3:python:function__entry
/str(arg1) == "validate_payment"/ {
  @watch[tid] = 1;
  @watch_start[tid] = nsecs;
}
usdt:/usr/bin/python3:python:function__entry /@watch[tid]/ {
  printf("%lld ENTER %s %s:%d\n",
    nsecs, str(arg1), str(arg0), arg2);
}
usdt:/usr/bin/python3:python:function__return /@watch[tid]/ {
  printf("%lld EXIT  %s\n", nsecs, str(arg1));
}
usdt:/usr/bin/python3:python:raise__exception /@watch[tid]/ {
  printf("\n!!! EXCEPTION DURING PAYMENT !!!\n");
  printf("type : %s\n", str(arg0));
  printf("after: %lldms\n", (nsecs-@watch_start[tid])/1000000);
  print(ustack(perf, 15));
  @watch[tid] = 0;
  exit();
}'
```

#### B. Flag suspiciously fast executions (indicating early return errors):
```bash
sudo bpftrace -p <PID> -e '
usdt:/usr/bin/python3:python:function__entry
/str(arg1) == "get_transaction_status"/ {
  @tx_start[tid] = nsecs;
  @tx_stack[tid] = ustack(perf, 8);
}
usdt:/usr/bin/python3:python:function__return
/str(arg1) == "get_transaction_status"/ {
  $dur = nsecs - @tx_start[tid];
  if ($dur < 100000) {
    printf("\n!!! SUSPICIOUSLY FAST RETURN !!!\n");
    printf("returned in %ldus — early return / branch issue?\n", $dur/1000);
    print(@tx_stack[tid]);
  }
  delete(@tx_start[tid]);
  delete(@tx_stack[tid]);
}'
```

---

### Phase 5 — Multi-Service Timestamp Correlation

Run a timestamped log on all machines concurrently:
```bash
sudo bpftrace -p <PID> -e '
usdt:/usr/bin/python3:python:function__entry {
  printf("SVC=%s TS=%lld ENTER %s %s:%d\n",
    comm, nsecs, str(arg1), str(arg0), arg2);
}
usdt:/usr/bin/python3:python:function__return {
  printf("SVC=%s TS=%lld EXIT  %s\n",
    comm, nsecs, str(arg1));
}
tracepoint:syscalls:sys_enter_connect /pid == $1/ {
  printf("SVC=%s TS=%lld CONNECT\n", comm, nsecs);
}' <PID> 2>&1 | tee /tmp/trace_<service_name>.log
```

Merge and sort all logs on one machine:
```bash
cat /tmp/trace_*.log | sort -k2 -t= | grep -v "^$"
```

---

### Logical Error Mental Model

```
Logical error symptoms:
├── Wrong value returned        → intercept write() — read actual payload
├── Wrong branch taken          → function returns too fast = early return
├── Missing call                → expected function never appears in trace
├── Called in wrong order       → timestamps show wrong sequence
├── Called with wrong args      → read() intercept shows wrong payload
└── Race condition              → two threads in same function simultaneously
```

```
START — something is wrong
│
├── Which service?
│   └── bytes_in/bytes_out per service → find where chain breaks
│
├── Which function?
│   └── full function trace filtered to your files only
│       → find the function that returns wrong/fast/never
│
├── What data?
│   └── intercept write()/read() syscalls → read actual payloads
│       → find where value becomes wrong
│
├── Which code path?
│   └── ustack on entry → who called this function
│       → wrong caller = wrong code path taken
│
├── Race condition?
│   └── count concurrent threads in same function
│       → > 1 simultaneously = race
│
└── Happens randomly?
    └── arm trigger on anomaly → capture only on bad execution
        → exit() after first capture = zero noise
```


