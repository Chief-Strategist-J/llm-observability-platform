import sys
import re
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class WireGrepService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, payload: str, pattern: str) -> None:
        print(f"Running wire-grep regex parser...")
        print(f"  Pattern: {pattern}")
        print(f"  Payload: {payload}")
        time.sleep(0.5)

        # Basic regex parsing matching PCRE style
        # Handled in python using re engine
        try:
            # support basic lookbehind and match resets where possible
            py_pattern = pattern.replace("\\K", "") # clean up for standard python re
            matches = re.findall(py_pattern, payload)
            
            print("\n=== Regex Wire Match Results ===")
            if matches:
                for idx, m in enumerate(matches, 1):
                    print(f"  Match {idx}: {m}")
            else:
                print("  No matches found on the wire payload.")
        except Exception as e:
            print(f"  Error parsing regex pattern: {e}")
