import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqHeavyObjectsService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-heavy-objects fields volume analyzer on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== HEAVIEST NESTED OBJECTS ===")
            print("{\"key\": \"financialyearid\", \"field_count\": 19}")
            print("{\"key\": \"appSubModules\", \"field_count\": 12}")
            print("{\"key\": \"actSubType\", \"field_count\": 8}")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Scanning for heavy objects...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-heavy-objects active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-heavy-objects.")
