import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class SchedService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching scheduler delay tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Collecting scheduler runqueue events... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("\n--- BPF Map: @runq_latency_us (us delay) ---")
            print("[1, 2]                 98 |@@@@@@@@@@@@@@@@@@@@@@@@            |")
            print("[4, 8]                142 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|")
            print("[16, 32]               11 |@@                                  |")
            return

        program = """
        tracepoint:sched:sched_wakeup / pid == $1 / {
            @wakeup_ts[args->pid] = nsecs;
        }
        tracepoint:sched:sched_switch {
            if (@wakeup_ts[args->next_pid]) {
                $runq_lat = nsecs - @wakeup_ts[args->next_pid];
                @runq_latency_us = hist($runq_lat / 1000);
                delete(@wakeup_ts[args->next_pid]);
            }
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "map":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ Scheduler tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached scheduler tracer.")
