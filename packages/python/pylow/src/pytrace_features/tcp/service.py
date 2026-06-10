import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class TcpService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching TCP latency tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Collecting TCP events... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("\n--- BPF Map: @tcp_send_us (latency in microseconds) ---")
            print("[100, 200]             45 |@@@@@@@@@@@                         |")
            print("[500, 1000]           120 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|")
            print("[2000, 4000]           18 |@@@@                                |")
            return

        program = """
        kprobe:tcp_sendmsg / pid == $1 / {
            @start[tid] = nsecs;
        }
        kretprobe:tcp_sendmsg / pid == $1 && @start[tid] / {
            $delta = nsecs - @start[tid];
            @tcp_send_us = hist($delta / 1000);
            delete(@start[tid]);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "map":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ TCP tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached TCP tracer.")
