import requests
import time
import uuid
import json

OTEL_COLLECTOR_URL = "http://localhost:4318/v1/traces"
DTAE_URL = "http://localhost:8090"
JAEGER_URL = "http://localhost:16686/api/traces"

def generate_otel_trace():
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    start_time = int((time.time() - 35) * 1e9) # 35s ago to trigger DTAE flush
    
    return {
        "resourceSpans": [{
            "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "verification-service"}}]},
            "scopeSpans": [{
                "spans": [{
                    "traceId": trace_id,
                    "spanId": span_id,
                    "name": "verify-operation",
                    "kind": 1,
                    "startTimeUnixNano": str(start_time),
                    "endTimeUnixNano": str(start_time + 500_000_000),
                    "status": {"code": 1}
                }]
            }]
        }]
    }, trace_id

def main():
    print("Step 1: Sending trace to OTel Collector...")
    payload, trace_id = generate_otel_trace()
    try:
        resp = requests.post(OTEL_COLLECTOR_URL, json=payload)
        resp.raise_for_status()
        print(f"Successfully sent trace {trace_id} to OTel Collector.")
    except Exception as e:
        print(f"Error sending to OTel: {e}")
        return

    print("\nStep 2: Waiting for propagation (5s)...")
    time.sleep(5)

    print("\nStep 3: Triggering DTAE Flush...")
    try:
        requests.post(f"{DTAE_URL}/api/v1/flush")
    except Exception as e:
        print(f"Error flushing DTAE: {e}")

    print("\nStep 4: Verifying in DTAE...")
    try:
        resp = requests.get(f"{DTAE_URL}/api/v1/analysis/results")
        results = resp.json().get("results", [])
        found_in_dtae = any(res.get("trace_id") == trace_id for res in results)
        if found_in_dtae:
            print(f"✅ Trace {trace_id} found in DTAE analysis results.")
        else:
            print(f"❌ Trace {trace_id} NOT found in DTAE yet.")
    except Exception as e:
        print(f"Error checking DTAE: {e}")

    print("\nStep 5: Verifying in Jaeger...")
    try:
        # Jaeger trace ID format is hex
        resp = requests.get(f"{JAEGER_URL}?service=verification-service")
        data = resp.json().get("data", [])
        found_in_jaeger = any(t.get("traceID") == trace_id for t in data)
        if found_in_jaeger:
            print(f"✅ Trace {trace_id} found in Jaeger.")
        else:
            print(f"❌ Trace {trace_id} NOT found in Jaeger yet.")
    except Exception as e:
        print(f"Error checking Jaeger: {e}")

if __name__ == "__main__":
    main()
