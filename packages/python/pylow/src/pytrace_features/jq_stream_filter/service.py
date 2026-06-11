import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqStreamFilterService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, pid: int) -> None:
        print(f"Attaching streaming parser (fromstream) on target PID {pid}...")
        time.sleep(0.5)

        # Emulating jq --stream path-value events
        stream_events = [
            [["payments", 0, "id"], "pay_1001"],
            [["payments", 0, "status"], "failed"],
            [["payments", 0, "amount"], 250.00],
            [["payments", 1, "id"], "pay_1002"],
            [["payments", 1, "status"], "completed"],
            [["payments", 1, "amount"], 500.00]
        ]

        print("\n=== Emitted Raw Streaming Parser Path-Value Pairs ===")
        for path, val in stream_events:
            print(f"  {path} => {val}")

        print("\n=== Stream-Filter Reconstruction (select status == failed) ===")
        reconstructed = []
        for idx in [0]: # simulated matched index
            item = {
                "id": stream_events[idx*3][1],
                "status": stream_events[idx*3 + 1][1],
                "amount": stream_events[idx*3 + 2][1]
            }
            reconstructed.append(item)
            print(f"  Reconstructed: {item}")
