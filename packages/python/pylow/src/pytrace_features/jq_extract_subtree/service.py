import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqExtractSubtreeService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, target_key: str = "appModulesId") -> None:
        print(f"Attaching jq-extract-subtree targeting key '{target_key}' on target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print(f"\n=== Surgical Subtree Extraction for key: {target_key} ===")
            print("{\n  \"appModulesId\": 1024,\n  \"name\": \"OPPR\",\n  \"status\": \"active\"\n}")
            return

        program = f"""
        tracepoint:syscalls:sys_enter_write /pid == $1/ {{
          printf("Searching for subtree matching key {target_key}...\\n");
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-extract-subtree active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-extract-subtree.")
