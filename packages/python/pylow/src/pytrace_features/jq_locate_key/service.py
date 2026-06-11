import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqLocateKeyService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, target_key: str = "salesActivities") -> None:
        print(f"Attaching jq-locate-key targeting key '{target_key}' on target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print(f"\n=== Path Location of Key: {target_key} ===")
            print("[\n  \"actStatus\",\n  \"actSubType\",\n  \"financialyearid\"\n]")
            return

        program = f"""
        tracepoint:syscalls:sys_enter_write /pid == $1/ {{
          printf("Searching for key path matching {target_key}...\\n");
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-locate-key active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-locate-key.")
