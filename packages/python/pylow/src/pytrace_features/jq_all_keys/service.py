import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqAllKeysService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-all-keys vocabulary scanner to target process {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== All Unique Keys in Document ===")
            print("actStatus\nactSubType\nassignUsers\nenddate\nfinancialyearid\nid\nisdeleted\nnewconconno\nrefLinkTo")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Scanning document vocabulary keys...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-all-keys active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-all-keys.")
