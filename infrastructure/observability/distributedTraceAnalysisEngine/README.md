# Distributed Trace Analysis Engine (DTAE)

A high-performance observability engine built in Rust for real-time distributed trace assembly, clustering, and anomaly detection.

## 🏗️ Architecture

DTAE follows the **Hexagonal Architecture** (Ports and Adapters) pattern, ensuring the core analysis logic remains isolated from infrastructure concerns.

```mermaid
graph TD
    subgraph Infrastructure
        OTLP[OTLP Receiver]
        JSON[JSON API]
        Store[Trace Store]
    end

    subgraph Domain
        direction TB
        Assembler[Trace Assembler]
        Extractor[Feature Extractor]
        Clustering[HDBSCAN Clusterer]
        Detectors[Anomaly Detectors]
        CriticalPath[Critical Path DP]
    end

    OTLP --> Assembler
    JSON --> Assembler
    Assembler --> Extractor
    Extractor --> Clustering
    Extractor --> Detectors
    Extractor --> CriticalPath
    Detectors --> Result[Analysis Result]
    Clustering --> Result
    CriticalPath --> Result
    Result --> Store
```

## 🔄 Sequence Diagram: Trace Analysis Pipeline

The following diagram illustrates the lifecycle of a trace from span ingestion to final analysis.

```mermaid
sequenceDiagram
    participant App as Application/Collector
    participant API as DTAE API (Axum)
    participant ASM as Trace Assembler
    participant PROC as Trace Processor
    participant DOM as Domain Logic
    participant INF as Infrastructure Adapters

    App->>API: POST /api/v1/spans (OTLP/JSON)
    API->>ASM: ingest_batch(spans)
    Note over ASM: Buffer spans by trace_id

    Loop Every Flush Interval
        API->>ASM: flush(watermark)
        ASM-->>API: List of complete/partial Traces
        
        Loop For each Trace
            API->>PROC: process(trace)
            PROC->>DOM: Extract 64-dim Fingerprint
            PROC->>INF: Cluster Assignment (HNSW)
            PROC->>INF: run_detectors(Latency, Structure, Error)
            PROC->>DOM: compute_critical_path()
            PROC-->>API: AnalysisResult
        End
        
        API->>INF: Store Traces & Results
    End
```

## 🚀 Key Use Cases

### 1. Automatic Bottleneck Identification
DTAE builds a Directed Acyclic Graph (DAG) for every trace and runs a Longest Path algorithm to find the "Critical Path". It accurately identifies which service is responsible for the majority of user-perceived latency.

### 2. Statistical Anomaly Detection (Signal Fusion)
Instead of simple thresholds, DTAE uses:
- **Log-normal Baselines**: For latency detection that accounts for natural variance.
- **KS-Test (Kolmogorov-Smirnov)**: To detect shifts in the structural distribution of traces within a cluster.
- **Novelty Detection**: Identifying error propagation paths never seen before.

### 3. Trace Fingerprinting & Clustering
Every trace is compressed into a 64-dimensional vector. **HDBSCAN** clustering then groups these fingerprints to find "normal" patterns and highlight "noise" (rare, anomalous traces) without requiring a pre-defined number of clusters (K).

## 🛠️ How to Use

### Installation

Ensure you have Rust installed (2024 edition):

```bash
cargo build --release
```

### Starting the Server

```bash
# Default port: 8090
./target/release/dtae-server
```

### Sending Data (OTLP)

DTAE can receive raw OTLP JSON exports from your OpenTelemetry Collector:

```bash
curl -X POST http://localhost:8090/api/v1/spans/otlp \
  -H "Content-Type: application/json" \
  -d @otlp_payload.json
```

### Triggering Analysis (Flush)

Traces are held in a stateful window. Trigger a flush to assemble and analyze them:

```bash
curl -X POST http://localhost:8090/api/v1/flush
```

### Retrieving Results

```bash
# Get all recent analysis results
curl http://localhost:8090/api/v1/analysis/results

# Get result for a specific trace
curl http://localhost:8090/api/v1/analysis/results/{trace_id}
```

### Using the Rust Client

```rust
use distributed_trace_analysis_engine::api::client::TraceAnalysisClient;

#[tokio::main]
async fn main() {
    let client = TraceAnalysisClient::new("http://localhost:8090");
    
    // Get results
    if let Ok(results) = client.get_results().await {
        for result in results {
            println!("Trace {}: Anomaly Score {}", result.trace_id.0, result.confidence);
        }
    }
}
```

## ⚙️ Configuration

Environment variables:
- `DTAE_BIND_ADDR`: Address to bind the server (default: `0.0.0.0:8090`).
- `RUST_LOG`: Logging level (default: `info`).

## 🧪 Testing

```bash
cargo test
```
