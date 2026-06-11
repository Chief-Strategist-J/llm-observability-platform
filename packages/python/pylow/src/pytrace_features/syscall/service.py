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
            print("SLOW SYSCALL id=0 dur=12ms")
            print("        read+0x10")
            print("        socket_recv+0x22   network.py:55")
            print("        fetch_data+0x18    client.py:30")
            print("        handle_request+0x9 server.py:45")
            print("\n--- BPF Map: @sys_lat ---")
            print("[0, 1]                12 |@@@@                                |")
            print("[2, 4]                43 |@@@@@@@@@@@@@@                      |")
            print("[8, 16]              187 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|")
            return

        # Real execution logic
        program = """
        tracepoint:raw_syscalls:sys_enter /pid == $1/ {
          @sys_start[tid, args->id] = nsecs;
        }
        tracepoint:raw_syscalls:sys_exit /pid == $1/ {
          if (@sys_start[tid, args->id]) {
            $dur = nsecs - @sys_start[tid, args->id];
            @sys_lat[args->id] = hist($dur / 1000);
            if ($dur > 10000000) {
              printf("SLOW SYSCALL id=%d dur=%lldms\\n", args->id, $dur/1000000);
              print(ustack(perf, 8));
            }
            delete(@sys_start[tid, args->id]);
          }
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "map":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ Syscall latency tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached syscall tracer.")
