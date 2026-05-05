# Domain Models and Core Algorithms

## Overview

This document provides an in-depth explanation of DTAE's domain models, data structures, and core algorithms. The domain layer contains the business logic that defines how traces are processed, analyzed, and clustered.

## Core Domain Models

### Trace and Span Models

#### Span

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Span {
    pub span_id: SpanId,           // Unique identifier for this span
    pub trace_id: TraceId,         // Parent trace identifier
    pub parent_span_id: Option<SpanId>, // Parent span (None for root)
    pub service_name: String,      // Service that generated this span
    pub operation_name: String,     // Operation/method name
    pub start_time_ns: u64,        // Start timestamp (nanoseconds since epoch)
    pub duration_ns: u64,          // Duration in nanoseconds
    pub status_code: SpanStatusCode, // Ok, Error, or Unset
    pub attributes: HashMap<String, String>, // Key-value metadata
}
```

**Key Concepts:**
- **Span ID**: Globally unique identifier (UUID v4)
- **Trace ID**: Groups all spans from a single distributed transaction
- **Parent-Child Relationship**: Forms the trace tree structure
- **Attributes**: Contextual information (user ID, request ID, etc.)

#### Trace

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trace {
    pub trace_id: TraceId,
    pub spans: Vec<Span>,
    pub tree: TraceTree,           // Computed tree structure
    pub status: TraceStatus,       // Complete or Partial
    pub assembled_at_ns: u64,      // When this trace was assembled
}
```

**Trace Tree Structure:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceTree {
    pub root_id: Option<SpanId>,   // Root span identifier
    pub depth: usize,              // Maximum tree depth
    pub width: usize,              // Maximum concurrent spans
    pub adjacency_list: HashMap<SpanId, Vec<SpanId>>, // Parent -> Children
}
```

### Trace Fingerprint Model

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceFingerprint {
    pub vector: Vec<f64>,          // 64-dimensional feature vector
}
```

#### Feature Vector Composition

| Feature Range | Type | Description |
|---------------|------|-------------|
| [0, 4] | Structural | span_count, depth, width, service_count, operation_hash |
| [5, 54] | Timing | total_duration, self_time_per_service, critical_path_ratio, parallel_efficiency |
| [55, 57] | Error | error_count, error_depth, error_propagation |
| [58, 63] | Reserved | Future features (memory usage, network hops, etc.) |

### Analysis Result Model

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisResult {
    pub trace_id: TraceId,
    pub cluster_id: i64,           // Assigned cluster (-1 for noise)
    pub anomaly_score: f64,        // Overall anomaly score (0-1)
    pub confidence: f64,           // Detection confidence (0-1)
    pub is_anomalous: bool,        // Combined anomaly determination
    pub signals: Vec<AnomalyScore>, // Individual detector outputs
    pub critical_path: CriticalPath, // Bottleneck analysis
    pub fingerprint: TraceFingerprint, // Computed fingerprint
    pub timestamp: String,         // Analysis timestamp
}
```

## Core Algorithms

### 1. Trace Assembly Algorithm

The trace assembly process reconstructs complete traces from buffered spans.

#### Algorithm Steps

1. **Span Buffering**: Spans are indexed by `trace_id` in memory buffers
2. **Watermark Evaluation**: Determine which traces are ready for assembly
3. **Tree Construction**: Build parent-child relationships
4. **Classification**: Mark as Complete (has root) or Partial (orphan)

#### Pseudocode

```rust
fn flush(assembler: &mut TraceAssembler, current_time: u64) -> AssemblyOutput {
    let watermark = current_time - WINDOW_DURATION;
    let orphan_watermark = current_time - ORPHAN_TIMEOUT;
    
    let mut complete = Vec::new();
    let mut partial = Vec::new();
    
    for (trace_id, buffer) in assembler.buffers.iter() {
        if buffer.has_root && buffer.first_seen <= watermark {
            // Complete trace: root span present + window expired
            let trace = build_trace(trace_id, &buffer.spans);
            complete.push(trace);
        } else if !buffer.has_root && buffer.first_seen <= orphan_watermark {
            // Partial trace: no root + orphan timeout
            let mut trace = build_trace(trace_id, &buffer.spans);
            trace.status = Partial;
            partial.push(trace);
        }
    }
    
    AssemblyOutput { complete_traces: complete, partial_traces: partial }
}
```

#### Tree Construction

```rust
fn build_tree(spans: &[Span]) -> TraceTree {
    let mut adjacency = HashMap::new();
    let mut depth = 0;
    let mut width = 0;
    let mut root_id = None;
    
    // Build adjacency list
    for span in spans {
        if let Some(ref parent_id) = span.parent_span_id {
            adjacency.entry(parent_id.clone())
                .or_insert_with(Vec::new)
                .push(span.span_id.clone());
        } else {
            root_id = Some(span.span_id.clone());
        }
    }
    
    // Calculate depth and width
    if let Some(ref root) = root_id {
        depth = calculate_depth(&adjacency, root);
        width = calculate_width(&adjacency, root);
    }
    
    TraceTree {
        root_id,
        depth,
        width,
        adjacency_list: adjacency,
    }
}
```

### 2. Feature Extraction Algorithm

Converts trace structure and timing into a 64-dimensional feature vector.

#### Structural Feature Extraction

```rust
fn extract_structural_features(trace: &Trace, features: &mut Vec<f64>) {
    // Feature 0: Total span count
    features.push(trace.spans.len() as f64);
    
    // Feature 1: Tree depth
    features.push(trace.tree.depth as f64);
    
    // Feature 2: Tree width  
    features.push(trace.tree.width as f64);
    
    // Feature 3: Service count
    let services: HashSet<&String> = trace.spans.iter()
        .map(|s| &s.service_name).collect();
    features.push(services.len() as f64);
    
    // Feature 4: Operation sequence hash
    let operations: Vec<&str> = trace.spans.iter()
        .map(|s| s.operation_name.as_str())
        .collect();
    features.push(hash_operation_sequence(&operations) as f64);
}
```

#### Timing Feature Extraction

```rust
fn extract_timing_features(trace: &Trace, features: &mut Vec<f64>) {
    let total_duration = trace.total_duration_ns() as f64;
    
    // Feature 5: Total duration
    features.push(total_duration);
    
    // Features 6-55: Self-time per service
    let services: HashSet<&String> = trace.spans.iter()
        .map(|s| &s.service_name).collect();
    
    for service in &services {
        let self_time = trace.spans.iter()
            .filter(|s| &s.service_name == *service)
            .map(|s| trace.self_time_ns(&s.span_id))
            .sum::<u64>() as f64;
        features.push(self_time);
    }
    
    // Pad remaining service slots with zeros
    while features.len() < 55 {
        features.push(0.0);
    }
    
    // Feature 55: Critical path ratio
    let critical_path_duration = estimate_critical_path(trace);
    let ratio = if total_duration > 0.0 {
        critical_path_duration / total_duration
    } else {
        0.0
    };
    features.push(ratio);
    
    // Feature 56: Parallel efficiency
    let total_work: f64 = trace.spans.iter()
        .map(|s| s.duration_ns as f64).sum();
    let service_count = services.len() as f64;
    let efficiency = if critical_path_duration > 0.0 && service_count > 0.0 {
        total_work / (critical_path_duration * service_count)
    } else {
        0.0
    };
    features.push(efficiency);
}
```

#### Error Feature Extraction

```rust
fn extract_error_features(trace: &Trace, features: &mut Vec<f64>) {
    // Feature 57: Error count
    let error_count = trace.spans.iter().filter(|s| s.is_error()).count();
    features.push(error_count as f64);
    
    // Feature 58: Error depth
    let error_depth = trace.spans.iter()
        .filter(|s| s.is_error())
        .map(|s| span_depth(trace, &s.span_id))
        .max()
        .unwrap_or(0);
    features.push(error_depth as f64);
    
    // Feature 59: Error propagation
    let propagated = detect_error_propagation(trace);
    features.push(if propagated { 1.0 } else { 0.0 });
}
```

### 3. HDBSCAN Clustering Algorithm

Density-based clustering that discovers natural cluster shapes and handles noise.

#### Core Concepts

- **Core Distance**: Distance to k-th nearest neighbor
- **Mutual Reachability Distance**: `max(core_a, core_b, distance(a,b))`
- **Minimum Spanning Tree**: Connects points with minimal mutual reachability
- **Cluster Hierarchy**: Extracted by cutting MST at different density levels

#### Algorithm Implementation

```rust
impl HdbscanClusterer {
    fn cluster(&mut self, fingerprints: &[TraceFingerprint]) -> Vec<i64> {
        let points: Vec<Vec<f64>> = fingerprints.iter()
            .map(|f| f.vector.clone()).collect();
        
        // Step 1: Compute core distances
        let core_distances = self.compute_core_distances(&points);
        
        // Step 2: Build mutual reachability MST
        let mst = self.build_mst(&points, &core_distances);
        
        // Step 3: Extract clusters from MST
        let labels = self.extract_clusters(&mst);
        
        // Step 4: Update centroids for assignment
        self.centroids = self.compute_centroids(&points, &labels);
        
        labels
    }
}
```

#### Mutual Reachability MST Construction

```rust
fn build_mst(points: &[Vec<f64>], core_distances: &[f64]) -> Vec<(usize, usize, f64)> {
    let n = points.len();
    let mut edges = Vec::new();
    
    // Prim's algorithm with mutual reachability distance
    let mut in_tree = vec![false; n];
    let mut min_dist = vec![f64::MAX; n];
    
    in_tree[0] = true;
    for j in 1..n {
        let mrd = mutual_reachability_distance(
            core_distances[0], core_distances[j],
            euclidean_distance(&points[0], &points[j])
        );
        min_dist[j] = mrd;
    }
    
    for _ in 1..n {
        let next = (0..n)
            .filter(|&i| !in_tree[i])
            .min_by_key(|&i| min_dist[i]);
        
        if let Some(next) = next {
            edges.push((parent[next], next, min_dist[next]));
            in_tree[next] = true;
            
            // Update distances
            for j in 0..n {
                if !in_tree[j] {
                    let mrd = mutual_reachability_distance(
                        core_distances[next], core_distances[j],
                        euclidean_distance(&points[next], &points[j])
                    );
                    if mrd < min_dist[j] {
                        min_dist[j] = mrd;
                        parent[j] = next;
                    }
                }
            }
        }
    }
    
    edges.sort_by_key(|e| e.2);
    edges
}
```

### 4. Critical Path Algorithm

Finds the true bottleneck in distributed traces using dynamic programming.

#### DAG Construction

```rust
fn build_dag(trace: &Trace) -> (DiGraph<SpanId, ()>, HashMap<SpanId, NodeIndex>) {
    let mut dag = DiGraph::new();
    let mut node_map = HashMap::new();
    
    // Add nodes
    for span in &trace.spans {
        let idx = dag.add_node(span.span_id.clone());
        node_map.insert(span.span_id.clone(), idx);
    }
    
    // Add edges (parent -> child)
    for span in &trace.spans {
        if let Some(ref parent_id) = span.parent_span_id {
            if let (Some(&parent_idx), Some(&child_idx)) = 
                (node_map.get(parent_id), node_map.get(&span.span_id)) {
                dag.add_edge(parent_idx, child_idx, ());
            }
        }
    }
    
    (dag, node_map)
}
```

#### Longest Path Dynamic Programming

```rust
fn longest_path_dp(dag: &DiGraph<SpanId, ()>, sorted: &[NodeIndex]) -> Vec<f64> {
    let mut dist = vec![0.0f64; dag.node_count()];
    
    // Process nodes in topological order
    for &node in sorted {
        let node_weight = dist[node.index()];
        
        // Update neighbors
        for neighbor in dag.neighbors(node) {
            let edge_weight = 1.0; // Can use duration weights
            let new_dist = node_weight + edge_weight;
            
            if new_dist > dist[neighbor.index()] {
                dist[neighbor.index()] = new_dist;
            }
        }
    }
    
    dist
}
```

#### Path Reconstruction

```rust
fn reconstruct_critical_path(
    trace: &Trace,
    dag: &DiGraph<SpanId, ()>,
    dist: &[f64],
    terminal: NodeIndex,
    span_map: &HashMap<NodeIndex, SpanId>
) -> Vec<CriticalPathNode> {
    let mut path = Vec::new();
    let mut current = Some(terminal);
    let total_duration = trace.total_duration_ns();
    
    while let Some(node_idx) = current {
        if let Some(span_id) = span_map.get(&node_idx) {
            if let Some(span) = trace.span_by_id(span_id) {
                let self_time = trace.self_time_ns(span_id);
                let contribution = if total_duration > 0 {
                    self_time as f64 / total_duration as f64
                } else {
                    0.0
                };
                
                path.push(CriticalPathNode {
                    span_id: span_id.clone(),
                    service: span.service_name.clone(),
                    operation: span.operation_name.clone(),
                    self_time_ns: self_time,
                    contribution,
                });
            }
        }
        
        // Move to predecessor with max distance
        let predecessors: Vec<NodeIndex> = dag.neighbors_directed(
            node_idx, petgraph::Direction::Incoming
        ).collect();
        
        current = predecessors.into_iter()
            .max_by(|&a, &b| dist[a.index()].partial_cmp(&dist[b.index()]).unwrap());
    }
    
    path.reverse();
    path
}
```

### 5. Anomaly Detection Algorithms

#### Latency Anomaly Detection

Uses log-normal distribution fitting with EWMA adaptation.

```rust
impl LatencyAnomalyDetector {
    fn detect(&self, trace: &Trace) -> Vec<AnomalyScore> {
        let mut scores = Vec::new();
        
        for span in &trace.spans {
            let key = format!("{}::{}", span.service_name, span.operation_name);
            
            if let Some(baseline) = self.baselines.get(&key) {
                if baseline.count >= 10 { // Minimum samples
                    let log_latency = (span.duration_ns as f64).ln();
                    let threshold = baseline.ewma_mean + 
                        self.sigma_multiplier * baseline.ewma_var.sqrt();
                    
                    if log_latency > threshold {
                        let score = (log_latency - baseline.ewma_mean) / 
                            baseline.ewma_var.sqrt();
                        
                        scores.push(AnomalyScore {
                            signal_name: format!("latency::{}", key),
                            score: score.min(2.0), // Cap at 2.0
                            threshold: 1.0,
                        });
                    }
                }
            }
        }
        
        scores
    }
}
```

#### Structural Anomaly Detection

Uses Kolmogorov-Smirnov test on sliding windows.

```rust
impl StructuralAnomalyDetector {
    fn detect(&self, trace: &Trace) -> Vec<AnomalyScore> {
        let cluster_id = self.current_cluster_map.get(&trace.trace_id.0)
            .copied().unwrap_or(-1);
        
        if cluster_id < 0 {
            return Vec::new(); // No cluster baseline
        }
        
        if let Some(window) = self.cluster_windows.get(&cluster_id) {
            if window.is_ready() {
                let ref_mean = Self::mean(&window.span_counts);
                let ref_std = Self::stddev(&window.span_counts);
                
                if ref_std > 0.0 {
                    let ks_stat = Self::ks_statistic(
                        &window.span_counts, ref_mean, ref_std
                    );
                    let critical = Self::ks_critical_value(
                        window.span_counts.len(), self.alpha
                    );
                    
                    if ks_stat > critical {
                        return vec![AnomalyScore {
                            signal_name: format!("structural::cluster_{}", cluster_id),
                            score: ks_stat / critical,
                            threshold: 1.0,
                        }];
                    }
                }
            }
        }
        
        Vec::new()
    }
}
```

#### Error Propagation Detection

Identifies novel error propagation paths.

```rust
impl ErrorPropagationDetector {
    fn detect(&self, trace: &Trace) -> Vec<AnomalyScore> {
        let propagations = self.extract_error_propagations(trace);
        let mut scores = Vec::new();
        
        for (source, target) in &propagations {
            let key = Self::pair_key(source, target);
            
            // Check if this is a new propagation path
            if !self.known_propagations.contains(&key) {
                scores.push(AnomalyScore {
                    signal_name: format!("error_propagation::{}", key),
                    score: 1.0,
                    threshold: 0.8,
                });
            }
        }
        
        scores
    }
    
    fn extract_error_propagations(&self, trace: &Trace) -> Vec<(String, String)> {
        let mut propagations = Vec::new();
        
        for span in &trace.spans {
            if !span.is_error() { continue; }
            
            if let Some(ref parent_id) = span.parent_span_id {
                if let Some(parent) = trace.span_by_id(parent_id) {
                    // Cross-service error propagation
                    if parent.is_error() && parent.service_name != span.service_name {
                        propagations.push((
                            parent.service_name.clone(),
                            span.service_name.clone(),
                        ));
                    }
                }
            }
        }
        
        propagations
    }
}
```

## Performance Characteristics

### Time Complexity

| Algorithm | Complexity | Notes |
|-----------|------------|-------|
| Trace Assembly | O(S) | S = number of spans |
| Feature Extraction | O(S + K) | K = number of services |
| HDBSCAN Clustering | O(N²) | N = number of traces |
| Critical Path DP | O(V + E) | V = spans, E = parent-child edges |
| Anomaly Detection | O(S) | Linear in span count |

### Space Complexity

| Component | Complexity | Description |
|-----------|------------|-------------|
| Span Buffer | O(B) | B = buffered spans |
| Feature Vectors | O(N × 64) | N = traces |
| Clustering State | O(C × 64) | C = cluster centroids |
| Anomaly Baselines | O(O) | O = unique operations |

### Memory Usage

Typical memory consumption for production workloads:

| Component | Memory (GB) | Scaling |
|-----------|-------------|---------|
| Span Buffers | 2-8 | Proportional to trace rate |
| Feature Storage | 1-4 | Proportional to trace count |
| Clustering State | 0.1-0.5 | Proportional to clusters |
| Anomaly Baselines | 0.5-2 | Proportional to operations |
| **Total** | **3.6-14.5** | **Depends on workload** |

## Configuration Parameters

### Assembly Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `window_duration_ns` | 30s | 10s-300s | Event-time window for complete traces |
| `orphan_timeout_ns` | 60s | 30s-600s | Timeout for partial traces |

### Clustering Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `min_cluster_size` | 50 | 10-500 | Minimum traces per cluster |
| `min_samples` | 10 | 5-50 | Core distance calculation |
| `distance_threshold` | 2.0 | 0.5-5.0 | Assignment threshold |

### Anomaly Detection Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `latency_sigma_multiplier` | 3.0 | 2.0-5.0 | Sensitivity for latency anomalies |
| `latency_ewma_lambda` | 0.99 | 0.9-0.999 | Adaptation rate for baselines |
| `structural_window_size` | 1000 | 100-5000 | Sliding window size |
| `structural_alpha` | 0.05 | 0.01-0.1 | KS test significance level |

## Extensibility

The domain models are designed for extensibility:

### Adding New Features

1. **Extend Feature Vector**: Update `FEATURE_DIMENSION` constant
2. **Add Extraction Logic**: Implement in `TraceFingerprint::extract()`
3. **Update Normalization**: Ensure proper scaling

### Adding New Detectors

1. **Implement AnomalyDetector Trait**:
   ```rust
   impl AnomalyDetector for CustomDetector {
       fn detect(&self, trace: &Trace) -> Vec<AnomalyScore> { ... }
       fn update_baseline(&mut self, trace: &Trace) { ... }
       fn signal_name(&self) -> &str { "custom" }
   }
   ```

2. **Register in Main**: Add to detector vector in `main.rs`

### Custom Clustering Algorithms

1. **Implement ClusterAssigner Trait**:
   ```rust
   impl ClusterAssigner for CustomClusterer {
       fn assign(&self, fingerprint: &TraceFingerprint) -> ClusterAssignment { ... }
       fn refit(&mut self, fingerprints: &[TraceFingerprint]) { ... }
   }
   ```

2. **Replace in Configuration**: Use custom clusterer in `TraceProcessor`
