import sys
import time
import json
import os
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

MOCK_PAYMENTS = [
    {"id": "pay_1", "amount": 150.00, "currency": "USD", "status": "completed"},
    {"id": "pay_2", "amount": 50.50, "currency": "EUR", "status": "completed"},
    {"id": "pay_3", "amount": 1250.00, "currency": "USD", "status": "failed"},
    {"id": "pay_4", "amount": 300.00, "currency": "EUR", "status": "pending"}
]

class JqReduceService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, pid: int) -> None:
        print(f"Executing jq-reduce metrics aggregator on target PID {pid}...")
        
        # Try to load target data from disk if it exists
        data = MOCK_PAYMENTS
        for filename in [f"/tmp/po{pid}.json", f"/tmp/r{pid}.json", "/tmp/r.json"]:
            if os.path.exists(filename):
                try:
                    with open(filename, "r") as f:
                        loaded = json.load(f)
                        if isinstance(loaded, list):
                            data = loaded
                        elif isinstance(loaded, dict) and "data" in loaded:
                            data = loaded["data"]
                    break
                except Exception:
                    pass

        # Compute reductions: sum all amounts by currency and running average
        currency_totals = {}
        status_max = {}
        running_sums = 0.0
        running_avgs = []

        for idx, item in enumerate(data, 1):
            amt = float(item.get("amount", 0.0) or 0.0)
            curr = item.get("currency", "USD")
            status = item.get("status", "completed")
            
            # Group totals
            currency_totals[curr] = currency_totals.get(curr, 0.0) + amt
            
            # Group max
            status_max[status] = max(status_max.get(status, 0.0), amt)
            
            # Running average
            running_sums += amt
            running_avgs.append({"idx": idx, "id": item.get("id"), "running_avg": round(running_sums / idx, 2)})

        print("\n=== Grouped Totals (reduce Currency) ===")
        print(json.dumps(currency_totals, indent=2))
        
        print("\n=== Running Maximums (reduce Status) ===")
        print(json.dumps(status_max, indent=2))

        print("\n=== Running Average State (foreach simulation) ===")
        for avg in running_avgs[:5]:
            print(f"  Item {avg['idx']} ({avg['id']}): running_avg = {avg['running_avg']}")
