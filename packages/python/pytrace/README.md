# pytrace

One CLI. Zero code changes. Full system flow visibility for any Python service or distributed system.

## How it works under the hood
Three layers working together:
- **Layer 1** → OTel auto-instrumentation (HTTP, DB, gRPC, queues — zero code changes)
- **Layer 2** → bpftrace USDT (Python function call tree, syscalls)
- **Layer 3** → pytrace CLI (stitches both, renders the flow)

---

## Complete CLI Command Reference

Here is the usage documentation for every command in the `pytrace` tool:

### 1. `pytrace attach <pid>`
Attach to any running Python process and start collecting trace logs immediately.
```bash
pytrace attach 4821
```

### 2. `pytrace flow`
Renders the complete execution flow tree (local/distributed spans & events) from the trace repository.
```bash
pytrace flow --last
```

### 3. `pytrace stitch`
Stitch distributed traces together across service boundaries using traceparent headers.
```bash
pytrace stitch --services api,worker,ml-service
```

### 4. `pytrace slow`
Continuously daemonize/monitor and surface slow execution paths exceeding a latency threshold.
```bash
pytrace slow --threshold 200ms --watch
```

### 5. `pytrace diff`
Compare execution flow metrics between versions or releases to detect regressions.
```bash
pytrace diff --before deploy-v1.2 --after deploy-v1.3
```

### 6. `pytrace syscall <pid>`
Trace syscall counts and histogram latency patterns for the target process.
```bash
pytrace syscall 4821
```

### 7. `pytrace malloc <pid>`
Profile allocations and heap sizing metrics.
```bash
pytrace malloc 4821
```

### 8. `pytrace tcp <pid>`
Trace outbound TCP latency.
```bash
pytrace tcp 4821
```

### 9. `pytrace io <pid>`
Trace Block and File I/O read/write latencies.
```bash
pytrace io 4821
```

### 10. `pytrace flame <pid>`
Generate sampling-based user/kernel stack flame graphs.
```bash
pytrace flame 4821 --duration 5
```

### 11. `pytrace sched <pid>`
Monitor runqueue latency and scheduling delays.
```bash
pytrace sched 4821
```

### 12. `pytrace pycall <pid>`
Profile Python `PyObject_Call` execution timings.
```bash
pytrace pycall 4821
```

### 13. `pytrace pyframe <pid>`
Log Python execution contexts at the frame level (file, function, line).
```bash
pytrace pyframe 4821
```

### 14. `pytrace pycpu <pid>`
Identify CPU hotspots in Python runtime execution stacks.
```bash
pytrace pycpu 4821
```

### 15. `pytrace pyexcept <pid>`
Trace raised and caught exceptions within Python virtual machine.
```bash
pytrace pyexcept 4821
```

### 16. `pytrace pyiowait <pid>`
Trace Python code blocked waiting on blocking I/O calls.
```bash
pytrace pyiowait 4821
```

### 17. `pytrace pygil <pid>`
Profile GIL lock acquisition delays and thread contention.
```bash
pytrace pygil 4821
```

### 18. `pytrace pyleak <pid>`
Profile heap allocations to detect memory leak patterns.
```bash
pytrace pyleak 4821
```

### 19. `pytrace pyreq <pid>`
Measure end-to-end request lifecycle breakdown.
```bash
pytrace pyreq 4821
```

### 20. `pytrace timeline <pid>`
Trace absolute chronological timeline call graph.
```bash
pytrace timeline 4821 --duration 5.0 --threshold 2.0
```

### 21. `pytrace pythread <pid>`
Trace thread-aware function call timelines with self-time.
```bash
pytrace pythread 4821
```

### 22. `pytrace pyasync <pid>`
Trace async await coroutine metrics and yields.
```bash
pytrace pyasync 4821
```

### 23. `pytrace pyargs <pid>`
Profile Python function call argument types and layout.
```bash
pytrace pyargs 4821
```

### 24. `pytrace pysyscall <pid>`
Profile syscalls attributed directly to Python frames.
```bash
pytrace pysyscall 4821
```

### 25. `pytrace pynplus1 <pid>`
Detect potential ORM loop-driven N+1 query patterns.
```bash
pytrace pynplus1 4821
```

### 26. `pytrace pygraph <pid>`
Trace hierarchical call relationships.
```bash
pytrace pygraph 4821
```

### 27. `pytrace pyanomaly <pid>`
Identify slow function calls using statistical baselines.
```bash
pytrace pyanomaly 4821
```

### 28. `pytrace pydash <pid>`
Stream traces directly to live curses dashboard.
```bash
pytrace pydash 4821
```

### 29. `pytrace pysingle <pid> <target_func>`
Trace single request / execution call tree with self time.
```bash
pytrace pysingle 4821 handle_request
```
