import sys
import time
import json
import os
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

MOCK_DATA = {
    "id": 462,
    "enddate": "2026-06-30",
    "actStatus": {
        "id": 1,
        "name": "In Progress"
    }
}

class JqFlatMapService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, pid: int) -> None:
        print(f"Executing JSON key flattener (flat-map) on PID {pid}...")
        time.sleep(0.5)

        data = MOCK_DATA
        for filename in [f"/tmp/po{pid}.json", f"/tmp/r{pid}.json", "/tmp/r.json"]:
            if os.path.exists(filename):
                try:
                    with open(filename, "r") as f:
                        data = json.load(f)
                    break
                except Exception:
                    pass

        # Flatten nested keys
        def flatten(d, parent_key='', sep='.'):
            items = []
            if isinstance(d, dict):
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    items.extend(flatten(v, new_key, sep=sep).items())
            elif isinstance(d, list):
                for idx, v in enumerate(d):
                    new_key = f"{parent_key}[{idx}]"
                    items.extend(flatten(v, new_key, sep=sep).items())
            else:
                items.append((parent_key, d))
            return dict(items)

        flat_payload = flatten(data)
        
        print("\n=== Serialized Dotted Flat Key-Value Map ===")
        print(json.dumps(flat_payload, indent=2))

        # Reverse operation (unflatten)
        unflattened = {}
        for k, v in flat_payload.items():
            parts = k.split(".")
            curr = unflattened
            for pt in parts[:-1]:
                if pt not in curr:
                    curr[pt] = {}
                curr = curr[pt]
            curr[parts[-1]] = v
            
        print("\n=== Reconstructed Nested Struct Output ===")
        print(json.dumps(unflattened, indent=2))
