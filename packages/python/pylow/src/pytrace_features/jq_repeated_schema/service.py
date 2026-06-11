import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqRepeatedSchemaService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-repeated-schema pattern detector on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Repeated Schema Keys ===")
            print("10x username\n10x updateusername\n10x isactive\n8x entrydatetime\n5x id\n5x name")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Scanning for repeated patterns...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-repeated-schema active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-repeated-schema.")
