# Performance Benchmarks

This page documents the performance characteristics of the LLM Observability SDK. Benchmarks are run against both the optimized `ReliableKafkaSpanReporter` and the standard OpenTelemetry SDK baseline to measure ingestion throughput, recovery speed, and resource metrics.

## Performance Dashboard

An interactive dark-mode HTML dashboard featuring throughput comparisons and tail latency profiles is generated automatically on test completion.

👉 **[Open Interactive Performance Dashboard](performance-report.html)**

---

## Performance Metrics Summary

The following metrics represent high-throughput ingestion and replay profiling with 5,000 spans under standard test conditions:

| Scenario | Throughput (spans/sec) | p50 Latency (ms) | p95 Latency (ms) | p99 Latency (ms) | Net Memory Delta |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **In-Memory Ingestion (Our SDK)** | **~91,745** | **< 0.01** | **< 0.01** | **~0.02** | **~2.77 MB** |
| **OpenTelemetry SDK (Baseline)** | **~9,539** | **~0.10** | **~0.16** | **~0.27** | **~8.36 MB** |
| **WAL Fallback Ingestion (Offline)** | **~7,743** | **< 0.01** | **< 0.01** | **~0.01** | **~2.30 MB** |
| **WAL Replay Recovery** | **~942,705** | **N/A** | **N/A** | **N/A** | **~0.00 MB** |

### Key Takeaways
- **9.6x Faster Ingestion**: Offloading Protobuf serialization (`_dict_to_proto_bytes`) to the background thread allows the caller to enqueue raw dictionaries almost instantly, reaching over 91k spans/sec compared to standard OTel's ~9.5k spans/sec.
- **Low Memory Footprint**: The SDK consumes under **3 MB** of net resident memory growth (VmRSS) during active ingestion cycles.
- **Robust Outage Fallback**: If the broker is unreachable, fallback to the SQLite WAL maintains a throughput of **~7.7k spans/sec**, ensuring the application is never blocked.
- **Sub-Microsecond Recovery**: Once connection is restored, the WAL logs are replayed back to Kafka at a recovery rate of over **940k spans/sec**.

---

## Running the Benchmarks

You can run the performance benchmark suite locally to re-evaluate throughput and resource metrics.

```bash
cd packages/python/instrumentation-sdk
PYTHONPATH=. .venv/bin/pytest tests/performance/test_reporter_performance.py
```
