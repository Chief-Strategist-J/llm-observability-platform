import sys
import time
import random
import json
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class ChaosRunService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, url: str, failure_rate: int = 30) -> None:
        print(f"Executing pipeline targeting '{url}' with {failure_rate}% chaos failure injection rate...")
        time.sleep(0.5)

        roll = random.randint(0, 99)
        if roll < failure_rate:
            failure_mode = roll % 4
            if failure_mode == 0:
                print("CHAOS: 500 Internal Server Error injected.")
                print("Response Headers: HTTP/1.1 500 Internal Server Error\nContent-Type: application/json")
                print("Body: {}")
            elif failure_mode == 1:
                print("CHAOS: Timeout injected. Sleeping for 5s...")
                time.sleep(5)
                print("Failed: Request timed out (configured max 3.5s timeout exceeded).")
            elif failure_mode == 2:
                print("CHAOS: 429 Too Many Requests injected.")
                print("Response Headers: HTTP/1.1 429 Too Many Requests\nRetry-After: 5\nContent-Type: application/json")
                print("Body: {\"error\": \"rate_limited\", \"retry_after\": 5}")
            else:
                print("CHAOS: Corrupt JSON body injected.")
                print("Response Headers: HTTP/1.1 200 OK\nContent-Type: application/json")
                print("Body: {id: 462, \"status\": \"invalid")
        else:
            print("✓ Request succeeded.")
            print("Response Headers: HTTP/1.1 200 OK\nContent-Type: application/json")
            print("Body: {\"status\": \"success\", \"id\": 462}")
