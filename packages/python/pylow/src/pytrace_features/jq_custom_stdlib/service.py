import sys
import time
import math
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqCustomStdlibService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, action: str, data_str: str) -> None:
        print(f"Executing custom stdlib helper '{action}'...")
        time.sleep(0.5)

        try:
            # parse numeric data
            items = [float(x.strip()) for x in data_str.split(",") if x.strip()]
        except Exception:
            items = [10.0, 20.0, 30.0, 40.0, 50.0]

        print(f"  Input Data: {items}")
        
        print("\n=== Result ===")
        if action == "percentile":
            p = 95
            items.sort()
            idx = (len(items) * p) / 100
            val = items[int(idx)] if idx < len(items) else items[-1]
            print(f"  95th Percentile: {val}")
        elif action == "zscore":
            mean = sum(items) / len(items)
            var = sum((x - mean) ** 2 for x in items) / len(items)
            std = math.sqrt(var)
            zscores = [round((x - mean) / std, 3) if std > 0 else 0.0 for x in items]
            print(f"  Mean: {mean} | Std Dev: {std:.3f}")
            print(f"  Z-Scores: {zscores}")
        elif action == "sliding_window":
            n = 3
            windows = [items[i:i+n] for i in range(len(items) - n + 1)]
            print(f"  Sliding Windows (size {n}): {windows}")
        else:
            print("Unknown helper. Supported actions: percentile, zscore, sliding_window")
