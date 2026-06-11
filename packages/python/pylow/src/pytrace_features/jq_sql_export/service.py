import sys
import time
import json
import os
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

MOCK_PAYMENTS = [
    {"id": "pay_1", "amount": 150.00, "currency": "USD", "status": "completed", "created_at": "2026-06-11T12:00:00Z"},
    {"id": "pay_2", "amount": 50.50, "currency": "EUR", "status": "completed", "created_at": "2026-06-11T12:05:00Z"}
]

class JqSqlExportService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, pid: int, table_name: str = "payments") -> None:
        print(f"Exporting structured records to SQL INSERT statements for table '{table_name}' (PID: {pid})...")
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

        print(f"\n=== Generated SQL Insert exposition (table: {table_name}) ===")
        for item in data:
            val_id = f"'{item.get('id')}'" if item.get('id') else "NULL"
            val_amt = float(item.get('amount', 0.0) or 0.0)
            val_curr = f"'{item.get('currency')}'" if item.get('currency') else "NULL"
            val_stat = f"'{item.get('status')}'" if item.get('status') else "NULL"
            val_date = f"'{item.get('created_at')}'" if item.get('created_at') else "NULL"
            
            print(f"INSERT INTO {table_name} (id, amount, currency, status, created_at) VALUES ({val_id}, {val_amt}, {val_curr}, {val_stat}, {val_date});")
