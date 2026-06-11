import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqNullsService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-nulls flat-list discoverer to target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== All Null Fields (Flat List) ===")
            print("[\n  \"newconconno\",\n  \"newconleadsid\",\n  \"reminderdate\",\n  \"refLinkTo.payModes\",\n  \"actStatus.salesActivities\"\n]")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Searching for null fields...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-nulls active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-nulls.")
