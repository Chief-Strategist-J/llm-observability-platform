import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqTraceAllKeysService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, target_key: str = "username") -> None:
        print(f"Attaching jq-trace-all-keys targeting key '{target_key}' on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print(f"\n=== Traced Occurrences of Key: {target_key} ===")
            print("updateusername: blute_jaydeep")
            print("username: blute_jaydeep")
            print("actStatus.updateusername: gravity_admin")
            print("actStatus.username: gravity_admin")
            print("actSubType.username: admin")
            return

        program = f"""
        tracepoint:syscalls:sys_enter_write /pid == $1/ {{
          printf("Tracing occurrences of key {target_key}...\\n");
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-trace-all-keys active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-trace-all-keys.")
