import sys
import time
import json
import os
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

MOCK_PAYMENTS = [
    {"id": "pay_1", "amount": 150.00, "status": "completed"},
    {"id": "pay_2", "amount": 50.50, "status": "completed"},
    {"id": "pay_3", "amount": 1250.00, "status": "failed"},
    {"id": "pay_4", "amount": 300.00, "status": "pending"}
]

class JqEarlyExitService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, pid: int, threshold: float = 1000.0) -> None:
        print(f"Executing jq-early-exit (label-break) targeting threshold > {threshold} (PID: {pid})...")
        time.sleep(0.5)

        data = MOCK_PAYMENTS
        for filename in [f"/tmp/po{pid}.json", f"/tmp/r{pid}.json", "/tmp/r.json"]:
            if os.path.exists(filename):
                try:
                    with open(filename, "r") as f:
                        loaded = json.load(f)
                        if isinstance(loaded, list):
                            data = loaded
                    break
                except Exception:
                    pass

        # Early exit matching simulation
        match = None
        scanned = 0
        for item in data:
            scanned += 1
            amt = float(item.get("amount", 0.0) or 0.0)
            if amt > threshold:
                match = item
                break  # label-break exit

        print("\n=== Label-Break Early Exit Result ===")
        if match:
            print(f"  ✓ Found target matching item: {json.dumps(match)}")
            print(f"  ✓ Performance: Early exited after scanning {scanned}/{len(data)} items (avoided redundant lookups)")
        else:
            print(f"  ✗ No items matched the threshold of {threshold} (Scanned {scanned} items)")
