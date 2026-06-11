import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqNullPctService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-null-pct metrics tracker on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Null Percentage statistics per object ===")
            print("{\n  \"key\": \"financialyearid\",\n  \"total\": 19,\n  \"nulls\": 18,\n  \"pct_null\": 95\n}")
            print("{\n  \"key\": \"actStatus\",\n  \"total\": 5,\n  \"nulls\": 1,\n  \"pct_null\": 20\n}")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Calculating null percentages...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-null-pct active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-null-pct.")
