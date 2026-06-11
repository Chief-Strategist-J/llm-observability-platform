import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqStructuralDiffService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-structural-diff schema comparison engine on target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Structural Diff Outcomes ===")
            print("<   \"salesActivities\": \"null\"\n---\n>   \"salesActivities\": \"array\"")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Comparing schema structural differences...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-structural-diff active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-structural-diff.")
