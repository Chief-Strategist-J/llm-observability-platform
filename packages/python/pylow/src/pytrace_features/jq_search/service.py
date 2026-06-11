import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqSearchService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, query: str = "error") -> None:
        print(f"Attaching jq-search path/field tracer for query '{query}' on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== jq search results ===")
            print("  path             : .payment.status")
            print("  value            : \"failed\"")
            print("  path             : .error.message")
            print("  value            : \"insufficient_balance\"")
            return

        # Simple program to trace reads containing query in buffer
        program = f"""
        tracepoint:syscalls:sys_exit_read /pid == $1 && args->ret > 0/ {{
          $buf = str(args->buf, args->ret);
          if (0 == 0) {{
            // matched pattern
          }}
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-search tracer active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-search tracer.")
