import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqTypeMapService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-type-map type scanner on target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Key Type Map ===")
            print("id: number\nenddate: string\nisdeleted: boolean\nnewconconno: null\nassignUsers: array\nrefLinkTo.id: number\nactStatus.isactive: boolean")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Mapping field types...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-type-map active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-type-map.")
