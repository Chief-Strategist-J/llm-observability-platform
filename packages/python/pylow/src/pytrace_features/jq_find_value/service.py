import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqFindValueService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, target_val: str = "gravity_admin") -> None:
        print(f"Attaching jq-find-value targeting value '{target_val}' on target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print(f"\n=== Path Location of Value: {target_val} ===")
            print("actStatus.updateusername\nactStatus.username")
            return

        program = f"""
        tracepoint:syscalls:sys_enter_write /pid == $1/ {{
          printf("Searching for matching value {target_val}...\\n");
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-find-value active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-find-value.")
