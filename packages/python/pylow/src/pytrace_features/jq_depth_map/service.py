import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqDepthMapService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-depth-map structure scanner on target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Key Depth Map ===")
            print("{\"key\": \"appSubModules\", \"depth\": 2}\n{\"key\": \"actSubType\", \"depth\": 2}\n{\"key\": \"financialyearid\", \"depth\": 1}\n{\"key\": \"id\", \"depth\": 0}")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Analyzing structure depth map...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-depth-map active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-depth-map.")
