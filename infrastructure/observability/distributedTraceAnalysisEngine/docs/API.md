# DTAE API Documentation

## Overview

The DTAE REST API provides endpoints for trace ingestion, analysis, and querying. All endpoints return JSON responses and follow RESTful conventions.

## Base URL

```
http://localhost:8090/api/v1
```

## Authentication

Currently, DTAE does not implement authentication. All endpoints are publicly accessible. In production deployments, consider adding API key or OAuth authentication.

## Response Format

All responses follow a consistent structure:

```json
{
  "data": { ... },
  "error": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

Error responses:
```json
{
  "data": null,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Detailed error description"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Endpoints

### Health Check

#### GET `/health`

Check if the DTAE service is healthy.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### Trace Ingestion

#### POST `/spans/otlp`

Ingest OTLP format spans from OpenTelemetry collectors.

**Headers:**
- `Content-Type: application/json`

**Body:**
```json
{
  "resource_spans": [
    {
      "resource": {
        "attributes": [
          {
            "key": "service.name",
            "value": { "string_value": "payment-service" }
          }
        ]
      },
      "scope_spans": [
        {
          "spans": [
            {
              "trace_id": "abc123...",
              "span_id": "def456...",
              "parent_span_id": "ghi789...",
              "name": "process_payment",
              "kind": 1,
              "start_time_unix_nano": "1640995200000000000",
              "end_time_unix_nano": "1640995201000000000",
              "status": { "code": 1 },
              "attributes": [
                {
                  "key": "payment.method",
                  "value": { "string_value": "credit_card" }
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

**Response:**
```json
{
  "accepted": 42,
  "message": "Spans processed successfully"
}
```

#### POST `/spans/json`

Ingest spans in simplified JSON format (useful for testing).

**Body:**
```json
[
  {
    "trace_id": "trace-123",
    "span_id": "span-456",
    "parent_span_id": "span-789",
    "service_name": "user-service",
    "operation_name": "authenticate_user",
    "start_time_ns": 1640995200000000000,
    "duration_ns": 1000000000,
    "status_code": "Ok",
    "attributes": {
      "user.id": "user-123"
    }
  }
]
```

---

### Trace Processing

#### POST `/flush`

Trigger trace assembly and analysis for buffered spans.

**Query Parameters:**
- `watermark_ns` (optional): Custom watermark timestamp in nanoseconds

**Response:**
```json
{
  "complete_traces": 15,
  "partial_traces": 3,
  "analysis_results": 18,
  "processing_time_ms": 45
}
```

---

### Analysis Results

#### GET `/analysis/results`

Get all recent analysis results.

**Query Parameters:**
- `limit` (optional): Maximum number of results (default: 100)
- `cluster_id` (optional): Filter by cluster ID
- `anomaly_only` (optional): Return only anomalous traces

**Response:**
```json
{
  "results": [
    {
      "trace_id": "trace-123",
      "cluster_id": 5,
      "anomaly_score": 0.85,
      "confidence": 0.92,
      "is_anomalous": true,
      "signals": [
        {
          "signal_name": "latency::user-service::authenticate_user",
          "score": 1.2,
          "threshold": 1.0,
          "is_anomalous": true
        }
      ],
      "critical_path": {
        "total_duration_ns": 5000000000,
        "critical_service": "database-service",
        "optimization_opportunity": true,
        "nodes": [
          {
            "span_id": "span-456",
            "service": "database-service",
            "operation": "query_user",
            "self_time_ns": 3000000000,
            "contribution": 0.6
          }
        ]
      },
      "fingerprint": {
        "vector": [0.1, 0.2, 0.3, ...]
      },
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ],
  "total_count": 150,
  "has_more": true
}
```

#### GET `/analysis/results/{trace_id}`

Get analysis result for a specific trace.

**Path Parameters:**
- `trace_id`: The trace ID to query

**Response:** Same structure as individual result in the list endpoint.

---

### Clustering Information

#### GET `/clusters`

Get information about trace clusters.

**Query Parameters:**
- `min_size` (optional): Minimum cluster size to include (default: 10)

**Response:**
```json
{
  "clusters": [
    {
      "cluster_id": 0,
      "member_count": 125,
      "centroid": [0.1, 0.2, 0.3, ...],
      "representative_trace_id": "trace-456",
      "dominant_service": "checkout-service",
      "avg_duration_ms": 2500,
      "error_rate": 0.02
    }
  ],
  "noise_count": 23,
  "total_traces": 148
}
```

#### GET `/clusters/{cluster_id}/members`

Get traces belonging to a specific cluster.

**Path Parameters:**
- `cluster_id`: The cluster ID to query

**Query Parameters:**
- `limit` (optional): Maximum number of traces (default: 50)

**Response:**
```json
{
  "cluster_id": 5,
  "member_count": 42,
  "traces": [
    {
      "trace_id": "trace-123",
      "duration_ms": 1500,
      "span_count": 8,
      "service_count": 3,
      "has_errors": false,
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### Anomaly Detection

#### GET `/anomalies`

Get recent anomaly detections.

**Query Parameters:**
- `limit` (optional): Maximum number of anomalies (default: 50)
- `signal_type` (optional): Filter by signal type (latency, structural, error_propagation)
- `min_score` (optional): Minimum anomaly score (default: 0.8)

**Response:**
```json
{
  "anomalies": [
    {
      "trace_id": "trace-789",
      "anomaly_score": 0.95,
      "confidence": 0.88,
      "detected_at": "2024-01-01T00:00:00Z",
      "signals": [
        {
          "signal_name": "latency::payment-service::process_payment",
          "score": 1.5,
          "threshold": 1.0,
          "is_anomalous": true
        }
      ],
      "trace_summary": {
        "duration_ms": 8000,
        "service_count": 4,
        "error_count": 1,
        "critical_path_bottleneck": "payment-service"
      }
    }
  ],
  "total_count": 15
}
```

---

### Performance Metrics

#### GET `/metrics`

Get system performance metrics.

**Response:**
```json
{
  "system": {
    "uptime_seconds": 86400,
    "memory_usage_mb": 512,
    "cpu_usage_percent": 15.5
  },
  "processing": {
    "traces_processed_total": 15000,
    "spans_processed_total": 125000,
    "avg_processing_time_ms": 35,
    "p99_processing_time_ms": 120
  },
  "clustering": {
    "active_clusters": 12,
    "avg_cluster_size": 85,
    "noise_rate": 0.08
  },
  "anomalies": {
    "anomalies_detected_today": 45,
    "false_positive_rate": 0.02,
    "avg_detection_confidence": 0.85
  }
}
```

---

### Configuration

#### GET `/config`

Get current configuration parameters.

**Response:**
```json
{
  "assembly": {
    "window_duration_ns": 30000000000,
    "orphan_timeout_ns": 60000000000
  },
  "clustering": {
    "min_cluster_size": 50,
    "min_samples": 10,
    "distance_threshold": 2.0
  },
  "anomaly_detection": {
    "latency_sigma_multiplier": 3.0,
    "latency_ewma_lambda": 0.99,
    "structural_window_size": 1000,
    "structural_alpha": 0.05
  }
}
```

#### PUT `/config`

Update configuration parameters (admin only).

**Body:**
```json
{
  "clustering": {
    "min_cluster_size": 75
  },
  "anomaly_detection": {
    "latency_sigma_multiplier": 2.5
  }
}
```

---

## Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_REQUEST` | Malformed request body or parameters | 400 |
| `TRACE_NOT_FOUND` | Requested trace ID does not exist | 404 |
| `CLUSTER_NOT_FOUND` | Requested cluster ID does not exist | 404 |
| `PROCESSING_ERROR` | Internal error during trace processing | 500 |
| `STORAGE_ERROR` | Error accessing trace storage | 500 |
| `CONFIGURATION_ERROR` | Invalid configuration parameters | 400 |

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production deployments:
- Ingestion endpoints: 1000 requests/minute
- Query endpoints: 100 requests/minute
- Configuration endpoints: 10 requests/minute

## SDK Examples

### Rust Client

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
    
    // Trigger flush
    if Ok(flush_result) = client.flush().await {
        println!("Processed {} traces", flush_result.complete_traces);
    }
}
```

### Python Client

```python
import requests
import json

class DTAEClient:
    def __init__(self, base_url="http://localhost:8090/api/v1"):
        self.base_url = base_url
    
    def get_results(self, limit=100):
        response = requests.get(f"{self.base_url}/analysis/results", 
                              params={"limit": limit})
        response.raise_for_status()
        return response.json()
    
    def flush(self):
        response = requests.post(f"{self.base_url}/flush")
        response.raise_for_status()
        return response.json()
    
    def get_anomalies(self, min_score=0.8):
        response = requests.get(f"{self.base_url}/anomalies",
                              params={"min_score": min_score})
        response.raise_for_status()
        return response.json()

# Usage
client = DTAEClient()
results = client.get_results()
anomalies = client.get_anomalies()
```

### JavaScript Client

```javascript
class DTAEClient {
    constructor(baseUrl = 'http://localhost:8090/api/v1') {
        this.baseUrl = baseUrl;
    }
    
    async getResults(limit = 100) {
        const response = await fetch(`${this.baseUrl}/analysis/results?limit=${limit}`);
        return await response.json();
    }
    
    async flush() {
        const response = await fetch(`${this.baseUrl}/flush`, { method: 'POST' });
        return await response.json();
    }
    
    async getAnomalies(minScore = 0.8) {
        const response = await fetch(`${this.baseUrl}/anomalies?min_score=${minScore}`);
        return await response.json();
    }
}

// Usage
const client = new DTAEClient();
const results = await client.getResults();
const anomalies = await client.getAnomalies();
```
