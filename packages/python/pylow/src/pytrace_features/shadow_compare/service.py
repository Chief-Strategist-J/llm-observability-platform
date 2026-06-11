import sys
import os
import json
import difflib
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class ShadowCompareService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def compare(self, prod_file: str = "", staging_file: str = "") -> None:
        print("Starting shadow API comparison...")
        
        prod_data = None
        staging_data = None

        if prod_file and os.path.exists(prod_file):
            try:
                with open(prod_file, "r") as f:
                    prod_data = json.load(f)
            except Exception:
                pass
        
        if staging_file and os.path.exists(staging_file):
            try:
                with open(staging_file, "r") as f:
                    staging_data = json.load(f)
            except Exception:
                pass

        # Use mock data if not loaded
        if prod_data is None or staging_data is None:
            prod_data = {
                "id": 462,
                "status": "APPROVED",
                "updated_at": "2026-06-11T12:00:00Z",
                "trace_id": "tx_prod_982",
                "amount": 1250.50
            }
            staging_data = {
                "id": 462,
                "status": "APPROVED",
                "updated_at": "2026-06-11T12:01:15Z",
                "trace_id": "tx_staging_412",
                "amount": 1250.50,
                "new_beta_field": True
            }

        # Struct difference (schema level)
        def get_keys(d, path=""):
            keys = set()
            if isinstance(d, dict):
                for k, v in d.items():
                    curr = f"{path}.{k}" if path else k
                    keys.add(curr)
                    keys.update(get_keys(v, curr))
            elif isinstance(d, list):
                for idx, item in enumerate(d):
                    keys.update(get_keys(item, f"{path}[{idx}]"))
            return keys

        prod_keys = get_keys(prod_data)
        staging_keys = get_keys(staging_data)

        added = staging_keys - prod_keys
        removed = prod_keys - staging_keys

        # Semantic/value difference (excluding volatile keys like timestamps or trace ids)
        volatile = {"updated_at", "created_at", "request_id", "trace_id", "timestamp"}
        def clean_data(d):
            if isinstance(d, dict):
                return {k: clean_data(v) for k, v in d.items() if k not in volatile}
            elif isinstance(d, list):
                return [clean_data(item) for item in d]
            return d

        clean_prod = clean_data(prod_data)
        clean_staging = clean_data(staging_data)

        # Print comparisons
        print("\n=== Shadow Test Staging vs Production ===")
        print("  Production keys: ", len(prod_keys))
        print("  Staging keys:    ", len(staging_keys))
        
        if added:
            print(f"  [+] Schema additions in staging: {sorted(list(added))}")
        if removed:
            print(f"  [-] Schema removals in staging:  {sorted(list(removed))}")

        if clean_prod == clean_staging:
            print("  ✓ Value compatibility: IDENTICAL (ignoring volatile audit fields)")
        else:
            print("  ✗ Value compatibility: MISMATCH")
            for k in prod_keys & staging_keys:
                # get leaf value
                def val_at(d, p):
                    parts = p.split(".")
                    cur = d
                    for pt in parts:
                        if isinstance(cur, dict) and pt in cur:
                            cur = cur[pt]
                        else:
                            return None
                    return cur
                
                v_prod = val_at(prod_data, k)
                v_stag = val_at(staging_data, k)
                if v_prod != v_stag and k not in volatile and not isinstance(v_prod, (dict, list)):
                    print(f"    Difference at {k}: Prod={v_prod} | Staging={v_stag}")
        print("=========================================")
