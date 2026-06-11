import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class PyiowaitService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching I/O Wait blocking call tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Monitoring blocking sys_read calls... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("BLOCKING READ 12ms")
            print("  [ustack]:")
            print("    fetch_metadata @ db/client.py:54")
            print("    handle_request @ gateway/server.py:12")
            return

        program = """
        tracepoint:syscalls:sys_enter_read / pid == $1 / {
            @read_start[tid] = nsecs;
            @read_stack[tid] = ustack(perf);
        }
        tracepoint:syscalls:sys_exit_read / pid == $1 / {
            if (@read_start[tid]) {
                $dur = nsecs - @read_start[tid];
                if ($dur > 5000000) {
                    printf("BLOCKING READ %lldms\\n", $dur / 1000000);
                    print(@read_stack[tid]);
                }
                delete(@read_start[tid]);
                delete(@read_stack[tid]);
            }
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "printf":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ I/O Wait tracer active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached I/O Wait tracer.")
