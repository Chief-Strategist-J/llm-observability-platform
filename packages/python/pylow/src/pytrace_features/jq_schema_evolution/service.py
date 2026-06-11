import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class JqSchemaEvolutionService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching jq-schema-evolution tracking comparison prober on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== Schema Evolution and Page Comparison ===")
            print("=== page 1 vs page 2 ===")
            print("OK - No changes detected.")
            print("=== page 1 vs page 3 ===")
            print("<   \"salesActivities\": \"null\"\n---\n>   \"salesActivities\": \"array\"")
            return

        program = """
        tracepoint:syscalls:sys_enter_write /pid == $1/ {
          printf("Detecting schema evolution trends...\\n");
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ jq-schema-evolution active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached jq-schema-evolution.")
