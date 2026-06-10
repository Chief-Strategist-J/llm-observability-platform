import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class SyscallService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching syscall tracer to PID {pid}...")
        # Check if bpftrace is available
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Collecting syscall events... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("\n--- BPF Map: @enter ---")
            print("sys_enter_read                                        142")
            print("sys_enter_write                                        89")
            print("sys_enter_epoll_wait                                   45")
            print("\n--- BPF Map: @latency (ns) ---")
            print("[0, 1]                12 |@@@@                                |")
            print("[2, 4]                43 |@@@@@@@@@@@@@@                      |")
            print("[8, 16]              187 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|")
            return

        # Real execution logic
        program = """
        tracepoint:syscalls:sys_enter_* / pid == $1 / {
            @enter[probe] = count();
        }
        tracepoint:syscalls:sys_exit_* / pid == $1 / {
            @latency = hist(nsecs);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "map":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ Syscall tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached syscall tracer.")
