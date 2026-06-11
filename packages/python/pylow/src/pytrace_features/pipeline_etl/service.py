import sys
import time
import json
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

MOCK_EXTRACTED = {
    "data": [
        {"paymentId": "pay_1", "total": "150.00", "currency_code": "usd", "state": "completed", "createdAt": "2026-06-11T12:00:00Z", "userId": "usr_99"},
        {"paymentId": "pay_2", "total": "-10.00", "currency_code": "eur", "state": "failed", "createdAt": "2026-06-11T12:05:00Z", "userId": "usr_99"},
        {"paymentId": "pay_3", "total": "500.00", "currency_code": "GBP", "state": "refunded", "createdAt": "2026-06-11T12:10:00Z", "userId": "usr_100"}
    ]
}

class PipelineEtlService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self) -> None:
        print("Executing Multi-stage Pipeline ETL (Extract, Normalize, Validate, Aggregate)...")
        time.sleep(0.5)

        # Stage 1: Extract
        print("\n=== Stage 1: Extract ===")
        print(f"  Extracted raw response with {len(MOCK_EXTRACTED['data'])} records.")

        # Stage 2: Normalize
        print("\n=== Stage 2: Normalize ===")
        normalized = []
        for item in MOCK_EXTRACTED["data"]:
            norm = {
                "id": item.get("paymentId"),
                "amount": float(item.get("total", 0.0)),
                "currency": item.get("currency_code", "USD").upper(),
                "status": item.get("state", "completed").lower(),
                "created_at": item.get("createdAt"),
                "user_id": item.get("userId")
            }
            normalized.append(norm)
            print(f"  Normalized record: {norm}")

        # Stage 3: Validate
        print("\n=== Stage 3: Validate (Split output streams) ===")
        valid = []
        invalid = []
        for norm in normalized:
            errors = []
            if norm["amount"] <= 0:
                errors.append("non_positive_amount")
            if norm["status"] not in ["completed", "failed", "pending"]:
                errors.append("invalid_status")
            
            if not errors:
                valid.append(norm)
                print(f"  [VALID] -> {norm}")
            else:
                norm["_errors"] = errors
                invalid.append(norm)
                print(f"  [INVALID] -> {norm}")

        # Stage 4: Aggregate
        print("\n=== Stage 4: Aggregate ===")
        totals = {}
        for v in valid:
            curr = v["currency"]
            totals[curr] = totals.get(curr, 0.0) + v["amount"]
        print(f"  Aggregation Totals: {totals}")
        
        print("\n=== Stage 5: Final ETL Summary Report ===")
        print(f"  Processed total normalized items: {len(normalized)}")
        print(f"  Successful (Valid): {len(valid)}")
        print(f"  Dropped (Invalid):  {len(invalid)}")
