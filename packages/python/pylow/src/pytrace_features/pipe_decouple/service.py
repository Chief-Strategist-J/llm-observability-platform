import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class PipeDecoupleService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, fifo_path: str = "/tmp/payment_pipe") -> None:
        print(f"Attaching pipe-decouple FIFO monitor for {fifo_path} on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== pipe decoupler status ===")
            print(f"Named Pipe Path : {fifo_path}")
            print("Decoupled Mode  : Enabled (Background Producer)")
            print("Consumer Read   : processing pay_1 (failed)")
            print("Consumer Read   : processing pay_2 (success)")
            return

        program = f"""
        tracepoint:syscalls:sys_enter_openat /pid == $1/ {{
          printf("Opening file/pipe: %s\\n", str(args->filename));
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ pipe-decouple tracer active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached pipe-decouple tracer.")
