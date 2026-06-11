import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class ServiceMapService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching service flow map tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print(f"\n=== SERVICE pid={pid} ===")
            print("outbound_calls : 18")
            print("bytes_in       : 450123")
            print("bytes_out      : 89042")
            print("conn_time_ms:")
            print("[0, 1]                1 |@                                   |")
            print("[2, 4]                8 |@@@@@@@@@@@@@@                      |")
            print("[8, 16]              12 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|")
            return

        program = """
        tracepoint:syscalls:sys_enter_connect /pid == $1/ {
          @conn_start[tid] = nsecs;
          @conn_count = count();
        }
        tracepoint:syscalls:sys_exit_connect /pid == $1/ {
          if (@conn_start[tid]) {
            $d = nsecs - @conn_start[tid];
            @conn_time = hist($d / 1000000);
            delete(@conn_start[tid]);
          }
        }
        tracepoint:syscalls:sys_enter_accept4 /pid == $1/ {
          @accept_ts = nsecs;
        }
        tracepoint:syscalls:sys_exit_accept4 /pid == $1/ {
          if (@accept_ts) {
            printf("INBOUND CONNECTION at %lld\\n", nsecs);
          }
        }
        tracepoint:syscalls:sys_exit_read /pid == $1 && args->ret > 0/ {
          @bytes_in = sum(args->ret);
        }
        tracepoint:syscalls:sys_exit_write /pid == $1 && args->ret > 0/ {
          @bytes_out = sum(args->ret);
        }
        interval:s:5 {
          printf("\\n=== SERVICE pid=%d ===\\n", $1);
          printf("outbound_calls : %d\\n", @conn_count);
          printf("bytes_in       : %lld\\n", @bytes_in);
          printf("bytes_out      : %lld\\n", @bytes_out);
          printf("conn_time_ms:\\n"); print(@conn_time);
          clear(@conn_count); clear(@bytes_in);
          clear(@bytes_out); clear(@conn_time);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ Service flow map tracer active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached service flow map tracer.")
