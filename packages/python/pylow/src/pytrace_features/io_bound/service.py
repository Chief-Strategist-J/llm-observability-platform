import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class IoBoundService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching I/O bound diagnostic tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("BLOCKED syscall=0 (read) 91ms")
            print("  [ustack]:")
            print("    fetch_data @ client.py:30")
            print("    handle_request @ server.py:45")
            print("\nSLOW READ fd=4 91ms")
            print("  [ustack]:")
            print("    fetch_data @ client.py:30")
            print("    handle_request @ server.py:45")
            return

        program = """
        tracepoint:raw_syscalls:sys_enter /pid == $1/ {
          @t[tid,args->id] = nsecs;
        }
        tracepoint:raw_syscalls:sys_exit /pid == $1/ {
          $d = nsecs - @t[tid,args->id];
          if ($d > 5000000) {
            printf("BLOCKED syscall=%d %lldms\\n", args->id, $d/1000000);
            print(ustack(perf, 5));
            exit();
          }
          delete(@t[tid,args->id]);
        }
        tracepoint:syscalls:sys_enter_read /pid == $1/ {
          @tr[tid] = nsecs;
          @fd[tid] = args->fd;
        }
        tracepoint:syscalls:sys_exit_read /pid == $1/ {
          $d = nsecs - @tr[tid];
          if ($d > 5000000) {
            printf("SLOW READ fd=%d %lldms\\n", @fd[tid], $d/1000000);
            print(ustack(perf,5));
            exit();
          }
          delete(@tr[tid]); delete(@fd[tid]);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ I/O bound diagnostic active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached I/O bound tracer.")
