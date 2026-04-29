import requests
import time
import uuid
import json

BASE_URL = "http://localhost:8090"

def generate_trace():
    trace_id = uuid.uuid4().hex
    start_time = int((time.time() - 35) * 1e9)
    
    spans = [
        {
            "traceId": trace_id,
            "spanId": uuid.uuid4().hex[:16],
            "name": "GET /api/v1/resource",
            "kind": 1,
            "startTimeUnixNano": str(start_time),
            "endTimeUnixNano": str(start_time + 500_000_000),
            "status": {"code": 1}
        }
    ]
    
    # Add a child span
    parent_id = spans[0]["spanId"]
    child_start = start_time + 50_000_000
    spans.append({
        "traceId": trace_id,
        "spanId": uuid.uuid4().hex[:16],
        "parentSpanId": parent_id,
        "name": "db_query",
        "kind": 1,
        "startTimeUnixNano": str(child_start),
        "endTimeUnixNano": str(child_start + 200_000_000),
        "status": {"code": 1}
    })
    
    return {
        "resourceSpans": [{
            "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "demo-service"}}]},
            "scopeSpans": [{"spans": spans}]
        }]
    }

def main():
    print(f"Checking DTAE health at {BASE_URL}...")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        resp.raise_for_status()
        print(f"Health: {resp.json()}")
    except Exception as e:
        print(f"Error: Server not reachable. Make sure it's running. {e}")
        return

    # 1. Ingest
    print("Sending demo trace...")
    payload = generate_trace()
    resp = requests.post(f"{BASE_URL}/api/v1/spans/otlp", json=payload)
    print(f"Ingest Response: {resp.json()}")

    # 2. Flush
    print("Triggering analysis flush...")
    resp = requests.post(f"{BASE_URL}/api/v1/flush")
    print(f"Flush Result: {resp.json()}")

    # 3. Get results
    print("Retrieving analysis results...")
    resp = requests.get(f"{BASE_URL}/api/v1/analysis/results")
    results = resp.json().get("results", [])
    print(f"Found {len(results)} results.")
    
    for res in results:
        tid = res.get("trace_id")
        is_anomaly = res.get("is_anomalous")
        confidence = res.get("confidence")
        print(f"Trace {tid}: Anomalous={is_anomaly}, Confidence={confidence:.2f}")

if __name__ == "__main__":
    main()
