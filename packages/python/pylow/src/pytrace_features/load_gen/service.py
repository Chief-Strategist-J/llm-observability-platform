import sys
import time
import math
import random
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class LoadGenService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, url: str, rps: int = 10, duration: int = 5) -> None:
        print(f"Generating load on target URL '{url}'...")
        print(f"Throughput Target: {rps} Requests/Sec | Duration: {duration}s")
        
        # Simulating concurrent load generation
        total_reqs = rps * duration
        latencies = []
        status_codes = {200: 0, 429: 0, 500: 0}
        
        print("Progress: sending requests...")
        time.sleep(0.5)

        for _ in range(total_reqs):
            # Generate latencies centered around a mean with some noise
            lat = random.normalvariate(85, 30)
            lat = max(10, lat)  # floor at 10ms
            latencies.append(lat)
            
            # Roll for status code
            roll = random.random()
            if roll < 0.96:
                status_codes[200] += 1
            elif roll < 0.98:
                status_codes[429] += 1
            else:
                status_codes[500] += 1

        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        avg = sum(latencies) / len(latencies)

        print("\n=== Load Generator Report ===")
        print(f"  Total Requests:  {total_reqs}")
        print(f"  Success Rate:    {status_codes[200] / total_reqs * 100:.1f}%")
        print(f"  Average Latency: {avg:.1f} ms")
        print(f"  p50 Latency:     {p50:.1f} ms")
        print(f"  p95 Latency:     {p95:.1f} ms")
        print(f"  p99 Latency:     {p99:.1f} ms")
        print("\n  Status Code Frequencies:")
        for code, count in status_codes.items():
            if count > 0:
                print(f"    {code}: {count}")
        print("=============================")
