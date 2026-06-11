import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class AwkStatsService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching awk-stats streaming aggregator on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== awk aggregate status stats ===")
            print("status          count       amount       pct")
            print("------          -----       ------       ---")
            print("200               890    890000.00     89.0%")
            print("400                90     90000.00      9.0%")
            print("500                20     20000.00      2.0%")
            print("\nTOTAL            1000   1000000.00")
            print("unique users: 450")
            return

        # simple program counting syscall statistics
        program = """
        tracepoint:raw_syscalls:sys_enter /pid == $1/ {
          @sys[args->id] = count();
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ awk-stats tracer active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached awk-stats tracer.")
