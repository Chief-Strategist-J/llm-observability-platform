import sys
import time
import json
import os
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

MOCK_PAYMENTS = [
    {"id": "pay_1", "amount": 150.00, "currency": "USD", "status": "completed"},
    {"id": "pay_2", "amount": 50.50, "currency": "EUR", "status": "completed"}
]

class JqFormatMatrixService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, pid: int, format_type: str = "csv") -> None:
        print(f"Converting JSON stream using Format Matrix (target format: {format_type})...")
        time.sleep(0.5)

        data = MOCK_PAYMENTS
        for filename in [f"/tmp/po{pid}.json", f"/tmp/r{pid}.json", "/tmp/r.json"]:
            if os.path.exists(filename):
                try:
                    with open(filename, "r") as f:
                        loaded = json.load(f)
                        if isinstance(loaded, list):
                            data = loaded
                        elif isinstance(loaded, dict) and "data" in loaded:
                            data = loaded["data"]
                    break
                except Exception:
                    pass

        print(f"\n=== Output Format Exposition: {format_type.upper()} ===")
        if format_type == "csv":
            print("id,amount,currency,status")
            for item in data:
                print(f"{item.get('id')},{item.get('amount')},{item.get('currency')},{item.get('status')}")
        elif format_type == "tsv":
            print("id\tamount\tcurrency\tstatus")
            for item in data:
                print(f"{item.get('id')}\t{item.get('amount')}\t{item.get('currency')}\t{item.get('status')}")
        elif format_type == "prometheus":
            print("# HELP payment_amount Metric listing payment amounts in standard cents unit")
            print("# TYPE payment_amount gauge")
            for item in data:
                amt_cents = int(float(item.get("amount", 0) or 0) * 100)
                print(f"payment_amount{{id=\"{item.get('id')}\",currency=\"{item.get('currency')}\",status=\"{item.get('status')}\"}} {amt_cents}")
        elif format_type == "elasticsearch":
            for item in data:
                meta = {"index": {"_index": "payments", "_id": item.get("id")}}
                body = {k: v for k, v in item.items() if k != "id"}
                print(json.dumps(meta))
                print(json.dumps(body))
        else:
            print("Unsupported format type. Supported formats: csv, tsv, prometheus, elasticsearch")
