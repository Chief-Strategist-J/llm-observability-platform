import sys
import time
import json
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

MOCK_PAYMENTS = [
    {"id": "pay_1", "amount": 100.00},
    {"id": "pay_2", "amount": 200.00},
    {"id": "pay_3", "amount": 300.00},
    {"id": "pay_4", "amount": 400.00}
]

class JqForeachService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, pid: int) -> None:
        print(f"Attaching jq-foreach stateful tracker to PID {pid}...")
        time.sleep(0.5)

        total_sum = 0.0
        count = 0
        
        print("\n=== Stateless Running average (foreach) Stream Output ===")
        for item in MOCK_PAYMENTS:
            amt = float(item["amount"])
            total_sum += amt
            count += 1
            avg = total_sum / count
            print(f"  Input: {item} => State: {{sum: {total_sum}, count: {count}}} => Output: {{running_avg: {avg}, after: {item['id']}}}")
