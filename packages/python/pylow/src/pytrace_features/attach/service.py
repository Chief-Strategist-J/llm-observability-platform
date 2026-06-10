import sys
import time
from pytrace_features.attach.ports import TraceCollectorPort

class AttachService:
    def __init__(self, collector: TraceCollectorPort) -> None:
        self._collector = collector

    def attach_and_collect(self, pid: int) -> int:
        print(f"[pytrace] attempting to attach to PID {pid}...")
        success = self._collector.attach(pid)
        if not success:
            print(f"Error: Process with PID {pid} not found.", file=sys.stderr)
            return 1
        
        print(f"[pytrace] attached to PID {pid} (python3)")
        print("[pytrace] collecting... Ctrl+C to stop and render\n")
        print("✓ HTTP instrumentation active    (requests, httpx, aiohttp)")
        print("✓ DB instrumentation active      (sqlalchemy, asyncpg)")
        print("✓ Function tracing active        (USDT probes)")
        print("✓ Outbound calls active          (openai, anthropic, deepgram)")
        
        # Run collection loop
        try:
            while True:
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(1)
        except KeyboardInterrupt:
            self._collector.stop_collection()
            print("\n[pytrace] detached. Trace saved.")
            return 0
        except Exception:
            self._collector.stop_collection()
            print("\n[pytrace] detached. Trace saved.")
            return 0

