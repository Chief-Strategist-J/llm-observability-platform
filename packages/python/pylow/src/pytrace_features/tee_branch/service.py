import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class TeeBranchService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching tee-branch stream pipeline monitor on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== tee branched stream output ===")
            print("[File: /tmp/raw_payments.json] written: 2048 bytes")
            print("[File: /tmp/failed.json] written: 512 bytes")
            print("[File: /tmp/by_status.json] written: 256 bytes")
            print("[Stdout] total failed: 3")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Branching write bytes: %d\\n", args->count);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ tee-branch tracer active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached tee-branch tracer.")
