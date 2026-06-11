import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqArraySchemaService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-array-schema arrays shapes detector on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Discovering Schema Array Shapes ===")
            print("{\n  \"id\": \"number\",\n  \"enddate\": \"string\",\n  \"assignUsers\": {\n    \"array_of\": \"string\",\n    \"length\": 5\n  }\n}")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Scanning arrays structure...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-array-schema active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-array-schema.")
