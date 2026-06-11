import sys
import time
import hmac
import hashlib
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class WebhookMockService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def listen(self, port: int = 9000, secret: str = "whsec_abc123") -> None:
        print(f"Starting simulated webhook receiver on port {port}...")
        print(f"Configured HMAC Secret: {secret}")
        time.sleep(0.5)

        # Mock receiving some incoming webhook events
        events = [
            {"event": "payment.completed", "id": "evt_9812", "amount": 1250.50},
            {"event": "payment.failed", "id": "evt_4123", "amount": 420.00}
        ]

        print("\nListening for incoming Webhooks (Press Ctrl+C to exit)...")
        time.sleep(1.0)
        
        for ev in events:
            payload = str(ev)
            signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            
            print(f"\n[HTTP POST] Received request at {time.strftime('%H:%M:%S')}")
            print(f"  Headers: X-Signature: sha256={signature} | Content-Type: application/json")
            print(f"  Payload: {payload}")
            print("  HMAC verification: ✓ SIGNATURE MATCHES & IS TRUSTED")
            print(f"  Action Taken: Processing event '{ev['event']}' successfully -> HTTP 200 OK")
            time.sleep(0.8)
        
        print("\nDetached webhook receiver.")
