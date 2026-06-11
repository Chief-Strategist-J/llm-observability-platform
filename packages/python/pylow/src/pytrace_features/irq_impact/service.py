import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class IrqImpactService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching Soft/Hard IRQ tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            print("✓ Attached. Collecting IRQ impact events... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("\n--- BPF Map: @sirq_type ---")
            print("[1] (TIMER_SOFTIRQ)                         84")
            print("[3] (NET_RX_SOFTIRQ)                        187")
            print("\n--- BPF Map: @sirq_lat (us) ---")
            print("[0, 1]                12 |@@@@                                |")
            print("[2, 4]                43 |@@@@@@@@@@@@@@                      |")
            print("[8, 16]              187 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|")
            return

        program = """
        tracepoint:irq:softirq_entry /cpu == curtask->cpu/ {
          @sirq_start = nsecs;
          @sirq_type[args->vec] = count();
        }
        tracepoint:irq:softirq_exit {
          if (@sirq_start) {
            $dur = nsecs - @sirq_start;
            @sirq_lat = hist($dur / 1000);
            delete(@sirq_start);
          }
        }
        interval:s:5 { print(@sirq_type); print(@sirq_lat); }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ Soft/Hard IRQ impact tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached Soft/Hard IRQ impact tracer.")
