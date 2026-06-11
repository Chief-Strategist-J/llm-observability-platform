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
        "name": "In Progress",
        "salesActivities": None,
        "username": "gravity_admin",
        "updateusername": None
    },
    "refLinkTo": {
        "id": 4,
        "payModes": None,
        "poNameAndNumber": "Nano Kernel Ltd - 11/26-27"
    }
}

class JqPathFindService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, pid: int, target_type: str = "null") -> None:
        print(f"Finding path nodes matching type '{target_type}' on PID {pid}...")
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

        def find_paths(val, current_path=[]):
            paths = []
            if val is None:
                if target_type == "null":
                    paths.append(current_path)
            elif isinstance(val, dict):
                if target_type == "object":
                    paths.append(current_path)
                for k, v in val.items():
                    paths.extend(find_paths(v, current_path + [k]))
            elif isinstance(val, list):
                if target_type == "array":
                    paths.append(current_path)
                for idx, item in enumerate(val):
                    paths.extend(find_paths(item, current_path + [idx]))
            elif isinstance(val, str):
                if target_type == "string":
                    paths.append(current_path)
            elif isinstance(val, (int, float)) and not isinstance(val, bool):
                if target_type in ["number", "numeric"]:
                    paths.append(current_path)
            elif isinstance(val, bool):
                if target_type == "boolean":
                    paths.append(current_path)
            return paths

        matched_paths = find_paths(data)

        print(f"\n=== Paths Matching Type: {target_type} ===")
        if matched_paths:
            for p in matched_paths:
                path_str = "".join([f"['{x}']" if isinstance(x, str) else f"[{x}]" for x in p])
                dotted_str = ".".join([str(x) for x in p])
                print(f"  Path:  {path_str}  (Dotted: .{dotted_str})")
        else:
            print("  No paths matched.")
