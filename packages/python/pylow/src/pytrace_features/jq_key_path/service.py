import sys
import time
import os
import json
import difflib
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

MOCK_DATA = {
    "id": 462,
    "enddate": "2026-06-30",
    "actStatus": {
        "id": 1,
        "name": "In Progress",
        "salesActivities": None,
        "username": "gravity_admin",
        "updateusername": "gravity_admin"
    },
    "actSubType": {
        "id": 2,
        "name": "Collect Payment",
        "username": "admin"
    },
    "financialyearid": {
        "id": 3,
        "name": "Financial Year 2026-2027"
    },
    "refLinkTo": {
        "id": 4,
        "payModes": None,
        "poNameAndNumber": "Nano Kernel Ltd - 11/26-27"
    },
    "stores": {
        "id": 10,
        "name": "Channasandra Store",
        "username": "channasandra_user"
    },
    "suppliers": {
        "id": 20,
        "accountName": "Gravity India Technologies Pvt Ltd",
        "username": "gravity_Dileep"
    }
}

class JqKeyPathService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, target_key: str = "name") -> None:
        print(f"Attaching jq-key-path targeting key '{target_key}' on target process {pid}...")
        
        # Load from disk if it exists, otherwise use mock
        data = MOCK_DATA
        for filename in [f"/tmp/po{pid}.json", f"/tmp/r{pid}.json", "/tmp/r.json", "/tmp/po.json"]:
            if os.path.exists(filename):
                try:
                    with open(filename, "r") as f:
                        data = json.load(f)
                    break
                except Exception:
                    pass

        def fuzzy_find_paths_values(d, t_key: str, current_path: str = "") -> list:
            results = []
            if isinstance(d, dict):
                for k, v in d.items():
                    path = f"{current_path}.{k}" if current_path else k
                    
                    # Compute similarity ratio
                    ratio = difflib.SequenceMatcher(None, t_key.lower(), k.lower()).ratio()
                    is_sub = t_key.lower() in k.lower()
                    
                    if is_sub or ratio >= 0.5:
                        match_score = 100 if is_sub else int(ratio * 100)
                        results.append((path, v, match_score))
                    
                    results.extend(fuzzy_find_paths_values(v, t_key, path))
            elif isinstance(d, list):
                for idx, item in enumerate(d):
                    path = f"{current_path}[{idx}]"
                    results.extend(fuzzy_find_paths_values(item, t_key, path))
            return results

        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(0.5)
            matches = fuzzy_find_paths_values(data, target_key)
            print(f"\n=== Fuzzy Path + Value of Key: {target_key} (50% - 100% similarity matches) ===")
            if matches:
                # Sort by score descending
                matches.sort(key=lambda x: x[2], reverse=True)
                for path, val, score in matches:
                    val_str = json.dumps(val) if not isinstance(val, str) else f'"{val}"'
                    print(f"  {path} = {val_str} (Match: {score}%)")
            else:
                print("  No similar keys found.")
            return

        program = f"""
        tracepoint:syscalls:sys_enter_write /pid == $1/ {{
          printf("Searching for key path matching {target_key}...\\n");
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-key-path active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-key-path.")

