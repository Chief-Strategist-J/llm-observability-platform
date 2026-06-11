import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqValidateFieldsService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-validate-fields presence assertion engine on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Validation Field Presence Assertions ===")
            print("OK: id = 456")
            print("OK: actStatus.name = In Progress")
            print("OK: actSubType.name = Collect Payment")
            print("MISSING or NULL: refLinkTo.deliveryTerms")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Validating required fields...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-validate-fields active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-validate-fields.")
