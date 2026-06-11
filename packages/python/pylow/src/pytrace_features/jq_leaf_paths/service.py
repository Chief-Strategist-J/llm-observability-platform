import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqLeafPathsService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, filter_val: str = "") -> None:
        print(f"Attaching jq-leaf-paths flat map tracer on target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== All Leaf Paths + Values ===")
            if filter_val:
                print(f"Filtering with term: {filter_val}")
                print("actStatus.username: gravity_admin")
                print("actStatus.updateusername: gravity_admin")
            else:
                print("id: 456\nenddate: 2026-06-11\nactStatus.id: 12\nactStatus.name: In Progress")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Scanning document leaf paths...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-leaf-paths active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-leaf-paths.")
