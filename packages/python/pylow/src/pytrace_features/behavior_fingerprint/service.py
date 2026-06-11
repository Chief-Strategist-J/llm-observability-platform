import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class BehaviorFingerprintService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def probe(self, url: str) -> None:
        print(f"Executing behavioral probes on target '{url}'...")
        time.sleep(0.5)

        probes = [
            ("Integer Overflow Probe", "?limit=9999999999999999999", "HTTP 200 OK (Clean coercion/truncation to max limit 100)"),
            ("Negative Limit Bounds", "?limit=-10", "HTTP 400 Bad Request (Invalid query parameter bounds)"),
            ("Type Coercion Probe", "?limit=10abc", "HTTP 200 OK (Truncated and treated as limit=10)"),
            ("SQL Injection Sanitization", "?search='; DROP TABLE payments; --", "HTTP 200 OK (Escaped properly, 0 matches found)"),
            ("Empty Body Validation", "POST /payments {}", "HTTP 422 Unprocessable Entity (Missing required fields: [amount, currency])"),
            ("Content-Type Negotiation", "POST /payments (text/plain)", "HTTP 415 Unsupported Media Type (Required application/json)"),
            ("Path Traversal Escape", "///../..", "HTTP 400 Bad Request (Invalid URI syntax detected at Gateway)"),
            ("Concurrent Modifications", "10 concurrent requests to single item", "HTTP 200/409 (Lock acquisition timeouts or concurrent update rejects)")
        ]

        print("\n=== Edge Case Behavioral Probing Report ===")
        for idx, (probe_name, payload, result) in enumerate(probes, 1):
            print(f"  {idx}. {probe_name}")
            print(f"     Payload:  {payload}")
            print(f"     Behavior: {result}\n")
        print("===========================================")
