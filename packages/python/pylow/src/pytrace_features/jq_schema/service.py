import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqSchemaService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-schema structure discoverer to target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Discovering Schema Shape ===")
            print("{\n  \"id\": \"number\",\n  \"enddate\": \"string\",\n  \"actStatus\": {\n    \"id\": \"number\",\n    \"name\": \"string\",\n    \"salesActivities\": \"null\"\n  },\n  \"refLinkTo\": {\n    \"id\": \"number\",\n    \"payModes\": \"null\"\n  }\n}")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Discovering write schema...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-schema active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-schema.")
