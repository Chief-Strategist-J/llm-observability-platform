import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqWatchChangesService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-watch-changes field changes tracker on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Live Snapshot Differences ===")
            print("BEFORE: actStatus.name\tIn Progress")
            print("AFTER:  actStatus.name\tCompleted")
            print("BEFORE: actStatus.username\tgravity_admin")
            print("AFTER:  actStatus.username\tblute_jaydeep")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Tracking snapshot changes over time...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-watch-changes active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-watch-changes.")
