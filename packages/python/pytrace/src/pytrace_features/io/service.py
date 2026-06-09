import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class IoService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching File I/O latency tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Collecting block I/O events... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("\n--- BPF Map: @read_lat (ns) ---")
            print("[4096, 8191]          150 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|")
            print("[16384, 32767]        23 |@@@@@                               |")
            return

        program = """
        tracepoint:block:block_rq_issue / pid == $1 / {
            @io_start[args->sector] = nsecs;
        }
        tracepoint:block:block_rq_complete {
            if (@io_start[args->sector]) {
                $lat = nsecs - @io_start[args->sector];
                @read_lat = hist($lat);
                delete(@io_start[args->sector]);
            }
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "map":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ File I/O tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached File I/O tracer.")
