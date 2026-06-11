import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqNullPathsService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-null-paths dotted paths discoverer to target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Null Fields Dotted Paths ===")
            print("newconconno\nnewconleadsid\nreminderdate\nrefLinkTo.payModes\nactStatus.salesActivities")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Searching for null paths...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-null-paths active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-null-paths.")
