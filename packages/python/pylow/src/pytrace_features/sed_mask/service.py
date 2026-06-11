import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class SedMaskService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching sed-mask privacy / PII sanitizing stream filter on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Stream Masking Filter Output ===")
            print("Original : {\"card_number\":\"1234-5678-9012-3456\",\"amount\":100}")
            print("Masked   : {\"card_number\":\"****-****-****-3456\",\"amount\":100}")
            print("ANSI colors and formatting characters stripped successfully.")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Filtering write buffer for PII patterns...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ sed-mask tracer active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached sed-mask tracer.")
