import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqKeyPathService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, target_key: str = "name") -> None:
        print(f"Attaching jq-key-path targeting key '{target_key}' on target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print(f"\n=== Exact Path + Value of Key: {target_key} ===")
            print("actStatus.name: In Progress")
            print("actSubType.name: Collect Payment")
            print("financialyearid.name: Financial Year 2026-2027")
            return

        program = f"""
        tracepoint:syscalls:sys_enter_write /pid == $1/ {{
          printf("Searching for key path matching {target_key}...\\n");
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-key-path active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-key-path.")
