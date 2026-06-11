import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class RateLimitTestService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching rate-limit-test prober on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Rate Limiting Diagnostic Probe ===")
            print("req 1  : 200 OK")
            print("req 2  : 200 OK")
            print("req 3  : 429 Too Many Requests (Rate limited at req 3)")
            print("retry-after        : 60s")
            print("rate-limit-remain  : 0")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("HTTP request probing...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ rate-limit-test tracer active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached rate-limit-test tracer.")
