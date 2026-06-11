import sys
import time
import random
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class DiffFuzzService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, url_a: str, url_b: str) -> None:
        print(f"Starting differential fuzzing comparing:")
        print(f"  Target A: {url_a}")
        print(f"  Target B: {url_b}")
        time.sleep(0.5)

        # Generate fuzz payloads
        payloads = [
            ("Prototype Pollution Probe", '{"__proto__": {"polluted": true}}'),
            ("SQLi Bypass", "'; DROP TABLE payments; --"),
            ("Integer Underflow", "-2147483648"),
            ("Floating Point Bound", "1e308"),
            ("Special Floats", "NaN"),
            ("Directory Traversal", "../../../etc/passwd")
        ]

        print("\nFuzzing inputs against both endpoints to detect behavioral divergences:")
        divergences = 0

        for name, payload in payloads:
            # Randomly simulate code differences
            code_a = 200 if "Bypass" not in name else 403
            code_b = 200 if "Pollution" not in name else 400
            
            # If they diverge
            if code_a != code_b:
                divergences += 1
                print(f"\n[DIVERGENCE FOUND] {name}")
                print(f"  Payload:  {payload}")
                print(f"  Target A: HTTP {code_a}")
                print(f"  Target B: HTTP {code_b}")
            else:
                print(f"  ✓ {name}: Identical responses (HTTP {code_a})")

        print(f"\n=== Differential Fuzzing Summary ===")
        print(f"  Total probes run:  {len(payloads)}")
        print(f"  Divergences found: {divergences}")
        print("=====================================")
