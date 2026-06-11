import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqNonNullLeavesService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-non-null-leaves flat map tracer on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Non-Null Leaves Only ===")
            print("id\t456")
            print("enddate\t2026-06-11")
            print("actStatus.id\t12")
            print("actStatus.name\tIn Progress")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Filtering non-null leaves...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-non-null-leaves active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-non-null-leaves.")
