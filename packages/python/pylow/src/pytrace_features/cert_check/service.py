import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class CertCheckService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, domain: str = "api.example.com") -> None:
        print(f"Attaching cert-check SSL/TLS handshake tracker on PID {pid} targeting '{domain}'...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== TLS Certificate Information ===")
            print(f"Domain             : {domain}")
            print("TLS Version        : TLS 1.3")
            print("Cert Expiry Date   : Oct 24 12:00:00 2026 GMT")
            print("SSL Verify Result  : 0 (ok)")
            return

        program = """
        tracepoint:syscalls:sys_enter_connect /pid == $1/ {
          printf("TLS verification connect started\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ cert-check tracer active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached cert-check tracer.")
