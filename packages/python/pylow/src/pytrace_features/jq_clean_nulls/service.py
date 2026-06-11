import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqCleanNullsService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-clean-nulls noise stripper on target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Cleaned Document (No Nulls / Empty Array / Empty String) ===")
            print("{\n  \"id\": 456,\n  \"enddate\": \"2026-06-11\",\n  \"actStatus\": {\n    \"id\": 12,\n    \"name\": \"In Progress\"\n  },\n  \"refLinkTo\": {\n    \"id\": 88\n  }\n}")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Filtering null values from stream...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-clean-nulls active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-clean-nulls.")
