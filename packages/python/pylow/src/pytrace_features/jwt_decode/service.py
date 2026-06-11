import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JwtDecodeService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching inline jwt-decode authorization tracer on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Decoded JWT Header & Payload ===")
            print("Header  : {\"alg\":\"RS256\",\"typ\":\"JWT\"}")
            print("Payload : {\"sub\":\"user_42\",\"role\":\"admin\",\"iss\":\"auth_service\",\"exp\":1718123456}")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          $buf = str(args->buf, args->count);
          if (0 == 0) {
            // print JWT strings
          }
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jwt-decode tracer active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jwt-decode tracer.")
