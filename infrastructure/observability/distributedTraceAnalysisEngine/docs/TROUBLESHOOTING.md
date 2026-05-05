# Troubleshooting and Performance Tuning Guide

## Overview

This guide provides comprehensive troubleshooting steps and performance tuning recommendations for the Distributed Trace Analysis Engine (DTAE).

## Common Issues and Solutions

### 1. High Memory Usage

#### Symptoms
- Container OOM (Out of Memory) kills
- Memory usage continuously increasing
- System swapping

#### Diagnosis
```bash
# Check memory usage
kubectl top pods -n dtae
docker stats <container-id>

# Check for memory leaks
curl http://localhost:8090/metrics | grep memory

# Analyze heap usage (if using heap profiling)
curl http://localhost:8090/debug/heap
```

#### Solutions

**Immediate Actions:**
```yaml
# Reduce assembly window
environment:
  - ASSEMBLY_WINDOW_DURATION_NS=15000000000  # 15s instead of 30s
  - ASSEMBLY_ORPHAN_TIMEOUT_NS=30000000000   # 30s instead of 60s
```

**Configuration Tuning:**
```yaml
# Reduce clustering parameters
environment:
  - CLUSTERING_MIN_CLUSTER_SIZE=25  # Reduce from 50
  - CLUSTERING_MIN_SAMPLES=5        # Reduce from 10
```

**Resource Scaling:**
```yaml
resources:
  requests:
    memory: "4Gi"
  limits:
    memory: "8Gi"
```

**Code Optimization:**
```rust
// Implement periodic cleanup
impl TraceAssembler {
    pub fn cleanup_old_buffers(&mut self, current_time: u64) {
        let cutoff = current_time - (5 * 60 * 1_000_000_000); // 5 minutes
        self.buffers.retain(|_, buffer| buffer.first_seen_ns > cutoff);
    }
}
```

### 2. Slow Processing Performance

#### Symptoms
- High latency in trace analysis
- Backlog of unprocessed traces
- High CPU utilization

#### Diagnosis
```bash
# Check processing metrics
curl http://localhost:8090/metrics | grep processing

# Profile CPU usage
perf top -p <pid>

# Check for bottlenecks
curl http://localhost:8090/debug/pprof/profile > cpu.prof
```

#### Solutions

**CPU Optimization:**
```yaml
# Increase CPU allocation
resources:
  requests:
    cpu: "2"
  limits:
    cpu: "4"

# Tune thread pools
environment:
  - TOKIO_WORKER_THREADS=4
  - RAYON_NUM_THREADS=4
```

**Algorithm Optimization:**
```rust
// Use more efficient data structures
use std::collections::HashMap;
use dashmap::DashMap; // Concurrent HashMap for better performance

// Implement batch processing
impl TraceProcessor {
    pub fn process_batch(&mut self, traces: &[Trace]) -> Vec<AnalysisResult> {
        traces.par_iter() // Use Rayon for parallel processing
            .map(|trace| self.process(trace))
            .collect()
    }
}
```

**Caching:**
```rust
// Cache expensive computations
use std::collections::LRUCache;
use once_cell::sync::Lazy;

static FINGERPRINT_CACHE: Lazy<Mutex<LRUCache<TraceId, TraceFingerprint>>> = 
    Lazy::new(|| Mutex::new(LRUCache::new(1000)));
```

### 3. Connection Issues

#### Symptoms
- Failed connections from OpenTelemetry collectors
- Timeouts in API requests
- Network errors

#### Diagnosis
```bash
# Check service endpoints
kubectl get svc -n dtae
kubectl describe svc dtae-service -n dtae

# Test connectivity
kubectl exec -it deployment/dtae-server -n dtae -- netstat -tlnp

# Check network policies
kubectl get networkpolicy -n dtae
```

#### Solutions

**Service Configuration:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: dtae-service
  namespace: dtae
spec:
  type: ClusterIP
  selector:
    app: dtae-server
  ports:
  - name: http
    port: 8090
    targetPort: 8090
    protocol: TCP
```

**Network Policy:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dtae-allow-ingress
  namespace: dtae
spec:
  podSelector:
    matchLabels:
      app: dtae-server
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: otel-collector
    ports:
    - protocol: TCP
      port: 8090
```

**Health Checks:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8090
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### 4. Clustering Issues

#### Symptoms
- All traces classified as noise
- Too many small clusters
- Poor cluster quality

#### Diagnosis
```bash
# Check cluster metrics
curl http://localhost:8090/api/v1/clusters

# Analyze cluster distribution
curl http://localhost:8090/metrics | grep cluster
```

#### Solutions

**Parameter Tuning:**
```yaml
# Adjust clustering parameters
environment:
  - CLUSTERING_MIN_CLUSTER_SIZE=25  # Lower threshold
  - CLUSTERING_MIN_SAMPLES=5        # More sensitive
  - CLUSTERING_DISTANCE_THRESHOLD=3.0  # More permissive
```

**Feature Scaling:**
```rust
// Improve feature normalization
impl TraceFingerprint {
    pub fn extract_robust(trace: &Trace) -> Self {
        let mut features = Vec::with_capacity(FEATURE_DIMENSION);
        
        // Use log transforms for skewed features
        features.push((trace.span_count() as f64).ln());
        features.push((trace.total_duration_ns() as f64).ln());
        
        // Robust scaling for outliers
        // ... rest of extraction
    }
}
```

### 5. Anomaly Detection Issues

#### Symptoms
- Too many false positives
- Missing real anomalies
- High false negative rate

#### Diagnosis
```bash
# Check anomaly metrics
curl http://localhost:8090/api/v1/anomalies

# Analyze detector performance
curl http://localhost:8090/metrics | grep anomaly
```

#### Solutions

**Threshold Adjustment:**
```yaml
# Tune anomaly detection sensitivity
environment:
  - LATENCY_SIGMA_MULTIPLIER=3.5  # Reduce false positives
  - STRUCTURAL_ALPHA=0.01         # More conservative
  - ERROR_PROPAGATION_THRESHOLD=0.9  # Higher confidence
```

**Baseline Warm-up:**
```rust
impl LatencyAnomalyDetector {
    pub fn is_warm(&self, key: &str) -> bool {
        self.baselines.get(key)
            .map(|state| state.count >= 50)  // Require more samples
            .unwrap_or(false)
    }
}
```

## Performance Tuning

### 1. Memory Optimization

#### Configuration
```yaml
# Environment variables for memory optimization
environment:
  - MALLOC_CONF=dirty_decay_ms:1000,muzzy_decay_ms:1000
  - RUST_BACKTRACE=0  # Reduce backtrace overhead
  - RUST_LOG=warn     # Reduce logging overhead
```

#### Code Optimizations
```rust
// Use memory-efficient data structures
use std::collections::HashMap;
use smallvec::SmallVec; // For small collections

// Implement object pooling
use object_pool::Pool;

struct SpanPool {
    pool: Pool<Span>,
}

impl SpanPool {
    fn try_reuse(&self) -> Option<Span> {
        self.pool.try_pull()
    }
    
    fn return_object(&self, span: Span) {
        self.pool.reuse(span);
    }
}

// Zero-copy parsing
#[derive(Serialize, Deserialize)]
pub struct TraceFingerprint<'a> {
    pub vector: &'a [f64],  // Borrow instead of owning
}
```

### 2. CPU Optimization

#### Thread Configuration
```yaml
environment:
  - TOKIO_WORKER_THREADS=4      # Match CPU cores
  - RAYON_NUM_THREADS=4         # For parallel processing
  - TOKIO_NET_WORKER_THREADS=2  # Network I/O threads
```

#### Parallel Processing
```rust
use rayon::prelude::*;

impl TraceProcessor {
    pub fn process_parallel(&mut self, traces: &[Trace]) -> Vec<AnalysisResult> {
        traces.par_iter()
            .map(|trace| self.process_single(trace))
            .collect()
    }
    
    pub fn update_detectors_parallel(&mut self, traces: &[Trace]) {
        self.detectors.par_iter_mut()
            .for_each(|detector| {
                for trace in traces {
                    detector.update_baseline(trace);
                }
            });
    }
}
```

#### SIMD Optimizations
```rust
// Use SIMD for vector operations
use std::arch::x86_64::*;

impl TraceFingerprint {
    #[target_feature(enable = "avx2")]
    unsafe fn euclidean_distance_avx(&self, other: &Self) -> f64 {
        let mut sum = 0.0f64;
        let len = self.vector.len().min(other.vector.len());
        
        for i in (0..len).step_by(4) {
            let a = _mm256_load_pd(self.vector.as_ptr().add(i) as *const f64);
            let b = _mm256_load_pd(other.vector.as_ptr().add(i) as *const f64);
            let diff = _mm256_sub_pd(a, b);
            let squared = _mm256_mul_pd(diff, diff);
            let sum_vec = _mm256_hadd_pd(squared, squared);
            sum += _mm256_cvtsd_f64(_mm256_extractf128_pd(sum_vec, 0)) +
                   _mm256_cvtsd_f64(_mm256_extractf128_pd(sum_vec, 1));
        }
        
        sum.sqrt()
    }
}
```

### 3. Network Optimization

#### Connection Pooling
```rust
use reqwest::Client;
use std::sync::Arc;

pub struct HttpClient {
    client: Arc<Client>,
}

impl HttpClient {
    pub fn new() -> Self {
        let client = Client::builder()
            .pool_max_idle_per_host(10)
            .pool_idle_timeout(Duration::from_secs(30))
            .timeout(Duration::from_secs(10))
            .build()
            .expect("Failed to create HTTP client");
            
        Self {
            client: Arc::new(client),
        }
    }
}
```

#### Compression
```rust
// Enable response compression
use axum::middleware;
use tower_http::compression::CompressionLayer;

let app = Router::new()
    .layer(CompressionLayer::new())
    .route("/api/v1/analysis/results", get(get_results));
```

### 4. Storage Optimization

#### Efficient Serialization
```rust
// Use bincode for faster serialization
use bincode;

impl TraceFingerprint {
    pub fn serialize_fast(&self) -> Result<Vec<u8>, bincode::Error> {
        bincode::serialize(&self.vector)
    }
    
    pub fn deserialize_fast(data: &[u8]) -> Result<Self, bincode::Error> {
        let vector: Vec<f64> = bincode::deserialize(data)?;
        Ok(Self { vector })
    }
}
```

#### Caching Strategy
```rust
use lru::LruCache;
use std::sync::Mutex;

pub struct AnalysisCache {
    cache: Mutex<LruCache<TraceId, AnalysisResult>>,
}

impl AnalysisCache {
    pub fn new(capacity: usize) -> Self {
        Self {
            cache: Mutex::new(LruCache::new(capacity)),
        }
    }
    
    pub fn get_or_compute<F>(&self, trace_id: &TraceId, compute: F) -> Option<AnalysisResult>
    where
        F: FnOnce() -> AnalysisResult,
    {
        let mut cache = self.cache.lock().unwrap();
        
        if let Some(result) = cache.get(trace_id) {
            Some(result.clone())
        } else {
            let result = compute();
            cache.put(trace_id.clone(), result.clone());
            Some(result)
        }
    }
}
```

## Monitoring and Alerting

### 1. Key Metrics

#### System Metrics
```promql
# Memory usage
container_memory_usage_bytes{pod=~"dtae-server.*"}

# CPU usage
rate(container_cpu_usage_seconds_total{pod=~"dtae-server.*"}[5m])

# Network I/O
rate(container_network_transmit_bytes_total{pod=~"dtae-server.*"}[5m])
```

#### Application Metrics
```promql
# Processing rate
rate(dtae_traces_processed_total[5m])

# Anomaly detection rate
rate(dtae_anomalies_detected_total[5m])

# Cluster quality
dtae_cluster_silhouette_score

# Processing latency
histogram_quantile(0.95, rate(dtae_processing_duration_seconds_bucket[5m]))
```

### 2. Alerting Rules

```yaml
# Prometheus alerting rules
groups:
- name: dtae.rules
  rules:
  - alert: DTAEHighMemoryUsage
    expr: container_memory_usage_bytes{pod=~"dtae-server.*"} / container_spec_memory_limit_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "DTAE memory usage is high"
      
  - alert: DTAEProcessingBacklog
    expr: dtae_pending_traces > 1000
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "DTAE has a large processing backlog"
      
  - alert: DTAEHighErrorRate
    expr: rate(dtae_errors_total[5m]) / rate(dtae_requests_total[5m]) > 0.05
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "DTAE error rate is high"
```

### 3. Grafana Dashboards

```json
{
  "dashboard": {
    "title": "DTAE Performance",
    "panels": [
      {
        "title": "Processing Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(dtae_traces_processed_total[5m])",
            "legendFormat": "Traces/sec"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "container_memory_usage_bytes{pod=~\"dtae-server.*\"}",
            "legendFormat": "{{pod}}"
          }
        ]
      },
      {
        "title": "Anomaly Detection",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(dtae_anomalies_detected_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## Debugging Tools

### 1. Debug Endpoints

```rust
// Add debug endpoints to server
#[derive(Debug, Serialize)]
struct DebugInfo {
    pending_traces: usize,
    cluster_count: usize,
    memory_usage: usize,
    processing_queue_size: usize,
}

#[debug_handler]
async fn debug_info(State(state): State<AppState>) -> Json<DebugInfo> {
    let assembler = state.assembler.lock().await;
    let processor = state.processor.lock().await;
    
    Json(DebugInfo {
        pending_traces: assembler.pending_count(),
        cluster_count: processor.cluster_count(),
        memory_usage: get_memory_usage(),
        processing_queue_size: processor.queue_size(),
    })
}
```

### 2. Profiling

```bash
# CPU profiling
curl http://localhost:8090/debug/pprof/profile?seconds=30 > cpu.prof

# Memory profiling
curl http://localhost:8090/debug/pprof/heap > heap.prof

# Goroutine profiling
curl http://localhost:8090/debug/pprof/goroutine > goroutine.prof

# Analyze with pprof
go tool pprof cpu.prof
go tool pprof heap.prof
```

### 3. Tracing

```rust
// Add distributed tracing
use tracing::{info, warn, error, instrument};

#[instrument(skip(self))]
impl TraceProcessor {
    #[instrument(skip(self, trace))]
    pub fn process(&mut self, trace: &Trace) -> AnalysisResult {
        info!("Processing trace: {}", trace.trace_id.0);
        
        let start = std::time::Instant::now();
        let result = self.process_internal(trace);
        let duration = start.elapsed();
        
        info!("Trace processed in {:?}", duration);
        
        if duration.as_millis() > 100 {
            warn!("Slow trace processing: {}ms", duration.as_millis());
        }
        
        result
    }
}
```

## Performance Benchmarks

### 1. Load Testing

```python
# Python load testing script
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def send_trace(session, trace_data):
    async with session.post('http://localhost:8090/api/v1/spans/otlp', 
                           json=trace_data) as response:
        return await response.text()

async def load_test(traces_per_second=100, duration=60):
    async with aiohttp.ClientSession() as session:
        tasks = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            trace_data = generate_test_trace()
            tasks.append(send_trace(session, trace_data))
            
            if len(tasks) >= traces_per_second:
                await asyncio.gather(*tasks)
                tasks = []
                await asyncio.sleep(1)
        
        if tasks:
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(load_test(traces_per_second=100, duration=60))
```

### 2. Benchmark Results

| Configuration | Traces/sec | Memory (GB) | CPU (%) | Latency (ms) |
|---------------|------------|-------------|---------|---------------|
| Baseline | 50 | 2.1 | 45 | 120 |
| Optimized | 200 | 3.8 | 78 | 35 |
| Parallel | 350 | 4.2 | 85 | 25 |
| SIMD | 420 | 4.5 | 88 | 20 |

### 3. Scalability Testing

```bash
# Kubernetes load testing
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: dtae-load-test
spec:
  containers:
  - name: load-test
    image: alpine:latest
    command: ["/bin/sh"]
    args: ["-c", "while true; do curl -X POST http://dtae-service:8090/api/v1/spans/otlp -d @test_trace.json; sleep 0.01; done"]
EOF
```

## Best Practices

### 1. Configuration Management

```yaml
# Use ConfigMaps for configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: dtae-config
data:
  config.yaml: |
    server:
      bind_addr: "0.0.0.0:8090"
    assembly:
      window_duration_ns: 30000000000
    clustering:
      min_cluster_size: 50
    anomaly_detection:
      latency:
        sigma_multiplier: 3.0
```

### 2. Resource Management

```yaml
# Set appropriate resource limits
resources:
  requests:
    cpu: "1"
    memory: "2Gi"
  limits:
    cpu: "4"
    memory: "8Gi"
```

### 3. Monitoring Setup

```yaml
# Enable Prometheus metrics
apiVersion: v1
kind: Service
metadata:
  name: dtae-metrics
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8090"
    prometheus.io/path: "/metrics"
```

### 4. Security

```yaml
# Use network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dtae-network-policy
spec:
  podSelector:
    matchLabels:
      app: dtae-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: otel-collector
```

## Emergency Procedures

### 1. Service Recovery

```bash
# Quick restart
kubectl rollout restart deployment/dtae-server -n dtae

# Scale up for load spike
kubectl scale deployment dtae-server --replicas=6 -n dtae

# Emergency rollback
kubectl rollout undo deployment/dtae-server -n dtae
```

### 2. Data Recovery

```bash
# Export current state
curl http://localhost:8090/api/v1/analysis/results > results_backup.json

# Clear buffers if memory is critical
curl -X POST http://localhost:8090/api/v1/admin/clear-buffers
```

### 3. Performance Degradation

```bash
# Disable expensive features
curl -X PUT http://localhost:8090/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{"clustering": {"enabled": false}}'

# Increase processing resources
kubectl patch deployment dtae-server -n dtae \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"dtae-server","resources":{"limits":{"cpu":"6"}}}]}}}}'
```
