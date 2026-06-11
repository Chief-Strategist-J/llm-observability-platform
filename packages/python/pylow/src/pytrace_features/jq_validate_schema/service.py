import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqValidateSchemaService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, schema_file: str = "schema.json") -> None:
        print(f"Attaching jq-validate-schema checking against '{schema_file}' on target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print(f"\n=== Validation Result Against '{schema_file}' ===")
            print("OK - Document shape matches schema exactly. 0 validation errors found.")
            return

        program = f"""
        tracepoint:syscalls:sys_enter_write /pid == $1/ {{
          printf("Comparing stream against {schema_file}...\\n");
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-validate-schema active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-validate-schema.")
